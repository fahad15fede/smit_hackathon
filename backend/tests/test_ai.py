import json
from datetime import date, timedelta

import httpx
import pytest

from app.ai.llm import GroqLLM, LLMReply, LLMUnavailable, TokenUsage, ToolCall, ToolResultMessage, ToolSpec, UserMessage, get_llm
from app.ai.tools import TOOL_SPECS
from app.main import app

from .conftest import auth, create_user


class ScriptedLLM:
    """Plays the model's side: each script step receives the conversation and returns a reply."""

    def __init__(self, *steps):
        self.steps = list(steps)
        self.calls = []

    def generate(self, *, system, messages, timeout, tools=None, json_schema=None):
        self.calls.append({"system": system, "messages": list(messages), "tools": tools, "json_schema": json_schema})
        step = self.steps.pop(0)
        return step(messages) if callable(step) else step


def tool_results(messages) -> dict:
    """The results of the most recent tool round, keyed by tool name."""
    last = next(m for m in reversed(messages) if isinstance(m, ToolResultMessage))
    return {call.name: result for call, result in last.results}


@pytest.fixture
def use_llm():
    def install(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        return llm

    yield install
    app.dependency_overrides.pop(get_llm, None)


def next_weekday(weekday: int) -> date:
    today = date.today()
    return today + timedelta(days=(weekday - today.weekday() - 1) % 7 + 1)


def test_chat_runs_tool_with_user_scope_and_logs(client, db, admin_token, use_llm):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    client.post("/api/departments", headers=auth(admin_token), json={"name": "Engineering"})
    llm = use_llm(
        ScriptedLLM(
            LLMReply(text=None, tool_calls=[ToolCall("get_headcount", {"department": "engineering"})]),
            lambda messages: LLMReply(
                text=f"Engineering has {tool_results(messages)['get_headcount']['active_employees']} active employees."
            ),
        )
    )

    response = client.post("/api/ai/chat", headers=auth(hr), json={"message": "How many active employees in Engineering?"})

    assert response.json() == {
        "answer": "Engineering has 0 active employees.",
        "ai_generated": True,
        "source": "ai",
        "tools_used": ["get_headcount"],
    }
    assert "COMPANY POLICY" in llm.calls[0]["system"]
    log = db.rows("ai_logs")[-1]
    assert (log["feature"], log["status"], log["tools_called"]) == ("chat", "ok", "get_headcount")


def test_employee_cannot_use_org_tools(client, admin_token, use_llm):
    employee = create_user(client, admin_token, "emp@acme.io")
    seen = {}

    def refuse(messages):
        seen.update(tool_results(messages))
        return LLMReply(text="Sorry, I can't share other employees' salaries.")

    use_llm(ScriptedLLM(LLMReply(text=None, tool_calls=[ToolCall("search_employees", {"query": "Ada"})]), refuse))

    response = client.post("/api/ai/chat", headers=auth(employee), json={"message": "What is Ada's salary?"})

    assert seen["search_employees"]["error"] == "not_permitted"
    assert response.json()["ai_generated"] is True


def test_my_leave_balance_counts_approved_leave(client, admin_token, use_llm):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    employee = create_user(client, hr, "emp@acme.io")
    sick = client.post("/api/leave-types", headers=auth(admin_token), json={"name": "Sick", "annual_quota": 8}).json()
    year = date.today().year
    leave = client.post(
        "/api/leaves",
        headers=auth(employee),
        json={"leave_type_id": sick["id"], "start_date": f"{year}-02-02", "end_date": f"{year}-02-03", "reason": "Flu"},
    ).json()
    client.post(f"/api/leaves/{leave['id']}/decision", headers=auth(hr), json={"approved": True})
    seen = {}

    def answer(messages):
        seen.update(tool_results(messages))
        return LLMReply(text="You have 6 sick days left.")

    use_llm(ScriptedLLM(LLMReply(text=None, tool_calls=[ToolCall("get_my_leave_balance", {"leave_type": "sick"})]), answer))
    client.post("/api/ai/chat", headers=auth(employee), json={"message": "How many sick leaves do I have left?"})

    (balance,) = seen["get_my_leave_balance"]["balances"]
    assert (balance["leave_type"], balance["used_approved"], balance["remaining"]) == ("Sick", 2, 6)


def test_attendance_rate_matches_dashboard(client, admin_token, use_llm):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    employee = create_user(client, hr, "emp@acme.io")
    client.post("/api/attendance/check-in", headers=auth(employee))
    seen = {}

    def answer(messages):
        seen.update(tool_results(messages))
        return LLMReply(text="ok")

    use_llm(ScriptedLLM(LLMReply(text=None, tool_calls=[ToolCall("get_attendance_summary", {})]), answer))
    client.post("/api/ai/chat", headers=auth(hr), json={"message": "What is this month's attendance rate?"})

    dashboard = client.get("/api/dashboard/organization", headers=auth(hr)).json()
    assert seen["get_attendance_summary"]["attendance_rate"] == dashboard["month_attendance_rate"]


def test_chat_falls_back_without_ai_key(client, db, admin_token):
    response = client.post("/api/ai/chat", headers=auth(admin_token), json={"message": "Who is late today?"})
    assert response.json()["ai_generated"] is False
    assert db.rows("ai_logs")[-1]["status"] == "fallback"


def test_rate_limit_per_user(client, admin_token):
    for _ in range(20):
        assert client.post("/api/ai/chat", headers=auth(admin_token), json={"message": "Who is late today?"}).status_code == 200
    blocked = client.post("/api/ai/chat", headers=auth(admin_token), json={"message": "Who is late today?"})
    assert blocked.status_code == 429


def test_leave_draft_retries_invalid_json_once(client, admin_token, use_llm):
    employee = create_user(client, admin_token, "emp@acme.io")
    casual = client.post("/api/leave-types", headers=auth(admin_token), json={"name": "Casual", "annual_quota": 10}).json()
    monday, tuesday = next_weekday(0), next_weekday(0) + timedelta(days=1)
    good = {"leave_type": "Casual", "start_date": monday.isoformat(), "end_date": tuesday.isoformat(), "reason": "Sister's wedding"}
    llm = use_llm(ScriptedLLM(LLMReply(text='{"leave_type": "Holiday"}'), LLMReply(text=json.dumps(good))))

    response = client.post(
        "/api/ai/leave-draft",
        headers=auth(employee),
        json={"text": "I need next Monday and Tuesday off for my sister's wedding"},
    ).json()

    assert response["ai_generated"] is True
    assert response["draft"] == {
        "leave_type_id": casual["id"],
        "leave_type_name": "Casual",
        "start_date": monday.isoformat(),
        "end_date": tuesday.isoformat(),
        "reason": "Sister's wedding",
    }
    assert len(llm.calls) == 2  # one retry
    assert client.get("/api/leaves/me", headers=auth(employee)).json() == []  # nothing saved


def test_leave_draft_gives_up_after_retry(client, admin_token, use_llm):
    employee = create_user(client, admin_token, "emp@acme.io")
    client.post("/api/leave-types", headers=auth(admin_token), json={"name": "Casual", "annual_quota": 10})
    use_llm(ScriptedLLM(LLMReply(text="not json"), LLMReply(text="still not json")))

    response = client.post("/api/ai/leave-draft", headers=auth(employee), json={"text": "off next week"}).json()

    assert response["draft"] is None and response["ai_generated"] is False


def test_dashboard_summary_bullets(client, admin_token, use_llm):
    bullets = ["Headcount is 1.", "No one is late today.", "There are 0 pending leave requests."]
    llm = use_llm(ScriptedLLM(LLMReply(text=json.dumps({"bullets": bullets}))))

    response = client.post("/api/ai/summary", headers=auth(admin_token)).json()

    assert response == {"bullets": bullets, "ai_generated": True, "message": None}
    assert '"headcount": 1' in llm.calls[0]["messages"][0].text


@pytest.mark.parametrize("message", ["Hi!", "hello there", "Thanks a lot", "ok", "bye", "What can you do?"])
def test_small_talk_never_reaches_the_model(client, db, admin_token, use_llm, message):
    llm = use_llm(ScriptedLLM())  # no scripted steps: any model call would fail the test

    response = client.post("/api/ai/chat", headers=auth(admin_token), json={"message": message}).json()

    assert response["source"] == "quick_reply" and response["ai_generated"] is False
    assert llm.calls == [] and db.rows("ai_logs") == []


def test_navigation_quick_reply_respects_role(client, admin_token, use_llm):
    employee = create_user(client, admin_token, "emp@acme.io")
    use_llm(ScriptedLLM())

    leave = client.post("/api/ai/chat", headers=auth(employee), json={"message": "How do I apply for leave?"}).json()

    assert leave["source"] == "quick_reply" and "Leave page" in leave["answer"]


def test_greeting_with_a_real_question_goes_to_the_model(client, admin_token, use_llm):
    llm = use_llm(ScriptedLLM(LLMReply(text="There are 1 active employees.")))

    response = client.post(
        "/api/ai/chat", headers=auth(admin_token), json={"message": "Hi, how many employees do we have?"}
    ).json()

    assert response["source"] == "ai" and len(llm.calls) == 1


def test_optional_tool_parameters_accept_null():
    headcount = next(spec for spec in TOOL_SPECS if spec.name == "get_headcount")
    assert headcount.parameters["properties"]["department"]["type"] == ["string", "null"]


def test_groq_client_retries_rejected_tool_call_and_parses_reply():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return httpx.Response(400, json={"error": {"code": "tool_use_failed", "message": "did not match schema"}})
        tool_call = {"id": "call_1", "type": "function", "function": {"name": "get_headcount", "arguments": '{"department": null}'}}
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [tool_call]}}]})

    llm = GroqLLM("key", "model", "https://groq.test/v1", transport=httpx.MockTransport(handler))
    spec = ToolSpec("get_headcount", "count", {"type": "object", "properties": {}})

    reply = llm.generate(system="sys", messages=[UserMessage("how many?")], timeout=5, tools=[spec])

    assert len(requests) == 2
    assert reply.tool_calls == [ToolCall("get_headcount", {"department": None}, id="call_1")]
    assert requests[0]["messages"][0] == {"role": "system", "content": "sys"}
    assert requests[0]["tools"][0]["function"]["name"] == "get_headcount"


def test_headcount_lists_every_department_including_empty_ones(client, admin_token, use_llm):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    for name in ("Engineering", "Sales", "Finance"):
        client.post("/api/departments", headers=auth(admin_token), json={"name": name})
    seen = {}

    def answer(messages):
        seen.update(tool_results(messages))
        return LLMReply(text="ok")

    llm = use_llm(ScriptedLLM(LLMReply(text=None, tool_calls=[ToolCall("get_headcount", {"department": None})]), answer))
    client.post("/api/ai/chat", headers=auth(hr), json={"message": "Headcount by department?"})

    result = seen["get_headcount"]
    assert result["by_department"] == {"Engineering": 0, "Finance": 0, "Sales": 0}
    assert result["without_department"] == 2  # the Admin and HR profiles have no department
    assert "Departments: Engineering, Finance, Sales" in llm.calls[0]["system"]


def test_department_partial_name_resolves(client, admin_token, use_llm):
    hr = create_user(client, admin_token, "hr@acme.io", role="hr")
    client.post("/api/departments", headers=auth(admin_token), json={"name": "Engineering"})
    seen = {}

    def answer(messages):
        seen.update(tool_results(messages))
        return LLMReply(text="ok")

    use_llm(ScriptedLLM(LLMReply(text=None, tool_calls=[ToolCall("get_headcount", {"department": "eng"})]), answer))
    client.post("/api/ai/chat", headers=auth(hr), json={"message": "How many in eng?"})

    assert seen["get_headcount"] == {"department": "Engineering", "active_employees": 0}


def test_token_usage_is_summed_into_ai_logs(client, db, admin_token, use_llm):
    use_llm(
        ScriptedLLM(
            LLMReply(text=None, tool_calls=[ToolCall("get_headcount", {})], usage=TokenUsage(1200, 30)),
            LLMReply(text="You have 1 active employee.", usage=TokenUsage(1300, 20)),
        )
    )
    client.post("/api/ai/chat", headers=auth(admin_token), json={"message": "How many employees?"})

    log = db.rows("ai_logs")[-1]
    assert (log["prompt_tokens"], log["completion_tokens"]) == (2500, 50)


def test_reasoning_effort_only_sent_to_reasoning_models():
    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "hi"}}]})

    for model in ("openai/gpt-oss-120b", "llama-3.3-70b-versatile"):
        GroqLLM("key", model, "https://groq.test/v1", transport=httpx.MockTransport(handler)).generate(
            system="s", messages=[UserMessage("hello")], timeout=5
        )

    assert bodies[0]["reasoning_effort"] == "low"
    assert "reasoning_effort" not in bodies[1]


def test_provider_rate_limit_gives_busy_message(client, admin_token, use_llm):
    def busy(messages):
        raise LLMUnavailable("429 rate limit", busy=True)

    use_llm(ScriptedLLM(busy))
    response = client.post("/api/ai/chat", headers=auth(admin_token), json={"message": "Who is late today?"}).json()

    assert response["source"] == "fallback" and "about a minute" in response["answer"]
