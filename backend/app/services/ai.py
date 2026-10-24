"""AI assistant features: tool-calling chat, dashboard summary and smart leave drafts.

Guardrails: the model never touches the database (tools call services with the user's scope),
never saves anything, has a hard deadline, is rate limited per user, and every call is logged
to ``ai_logs``. Any failure degrades to a friendly, non-AI response.
"""

import json
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError
from supabase import Client

from ..ai import prompts, quick_replies
from ..ai.llm import LLM, LLMReply, LLMUnavailable, Message, ModelMessage, TokenUsage, ToolResultMessage, UserMessage
from ..ai.tools import TOOL_SPECS, ToolContext, run_tool
from ..core.config import get_settings
from ..core.exceptions import RateLimitedError
from ..models import User
from ..repositories import ai_logs as ai_log_repo
from ..schemas.ai import ChatResponse, ChatTurn, LeaveDraft, LeaveDraftResponse, SummaryResponse
from . import dashboard as dashboard_service
from . import organization as organization_service
from .calendar import company_today
from .company import get_company

MAX_TOOL_ROUNDS = 4
CHAT_FALLBACK = "The assistant is unavailable right now. Please try again in a moment, or use the dashboard and reports."
BUSY_FALLBACK = "The assistant is handling a lot of requests right now. Please try again in about a minute."
SUMMARY_FALLBACK = "Could not generate a summary right now. The numbers on the dashboard are up to date."
LEAVE_FALLBACK = "I couldn't turn that into a leave request. Please fill in the form."

T = TypeVar("T", bound=BaseModel)

# Models often emit typographic look-alikes (non-breaking hyphens and spaces) that render oddly.
_TYPOGRAPHY = str.maketrans({"‐": "-", "‑": "-", "‒": "-", " ": " ", " ": " ", " ": " "})


def _tidy(text: str) -> str:
    return text.translate(_TYPOGRAPHY).strip()


class _Deadline:
    def __init__(self, seconds: float):
        self._started = time.monotonic()
        self._ends = self._started + seconds

    def remaining(self) -> float:
        remaining = self._ends - time.monotonic()
        if remaining < 1:
            raise LLMUnavailable("deadline exceeded")
        return remaining

    @property
    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self._started) * 1000)


class _Log:
    """Collects what happened during one AI call and writes a single ``ai_logs`` row."""

    def __init__(self, db: Client, user: User, feature: str, prompt: str):
        self.db, self.user, self.feature, self.prompt = db, user, feature, prompt
        self.tools: list[str] = []
        self.usage = TokenUsage()

    def track(self, reply: LLMReply) -> LLMReply:
        self.usage += reply.usage
        return reply

    def write(self, status: str, deadline: _Deadline | None = None) -> None:
        ai_log_repo.record(
            self.db,
            user_id=self.user.id,
            feature=self.feature,
            prompt=self.prompt,
            tools_called=self.tools,
            status=status,
            latency_ms=deadline.elapsed_ms if deadline else 0,
            prompt_tokens=self.usage.prompt_tokens,
            completion_tokens=self.usage.completion_tokens,
        )


def _enforce_rate_limit(log: _Log) -> None:
    limit = get_settings().ai_requests_per_hour
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    if ai_log_repo.count_since(log.db, log.user.id, since) >= limit:
        log.write("rate_limited")
        raise RateLimitedError(f"You have reached the assistant limit of {limit} requests per hour. Please try again later.")


def _generate_json(
    llm: LLM, log: _Log, deadline: _Deadline, system: str, prompt: str, schema: dict, parse: Callable[[dict], T]
) -> T:
    """Ask for JSON and validate it; on failure retry once with the error, then give up."""
    messages: list[Message] = [UserMessage(prompt)]
    for attempt in range(2):
        reply = log.track(llm.generate(system=system, messages=messages, timeout=deadline.remaining(), json_schema=schema))
        try:
            return parse(json.loads(reply.text or ""))
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            if attempt == 1:
                raise LLMUnavailable(f"invalid JSON output: {exc}") from exc
            messages += [
                ModelMessage(reply),
                UserMessage(f"That output was invalid ({exc}). Reply again with corrected JSON only."),
            ]
    raise AssertionError("unreachable")


# Chat ---------------------------------------------------------------------------------


def chat(db: Client, llm: LLM | None, user: User, message: str, history: list[ChatTurn]) -> ChatResponse:
    quick = quick_replies.match(message, user)
    if quick is not None:  # small talk, help, navigation: no model call, no rate limit, no ai_logs row
        return ChatResponse(answer=quick, ai_generated=False, source="quick_reply")

    log = _Log(db, user, "chat", message)
    _enforce_rate_limit(log)
    deadline = _Deadline(get_settings().ai_timeout_seconds)
    try:
        if llm is None:
            raise LLMUnavailable("no AI key configured")
        company = get_company(db)
        today = company_today(company)
        ctx = ToolContext(db=db, user=user, company=company, today=today)
        departments = [d.name for d in organization_service.list_departments(db)] if ctx.is_manager else None
        system = prompts.chat_system_prompt(user, company, today, prompts.policy_text(db, company, today), departments)

        messages: list[Message] = [
            UserMessage(turn.text) if turn.role == "user" else ModelMessage(LLMReply(text=turn.text))
            for turn in history
        ]
        messages.append(UserMessage(message))
        for _ in range(MAX_TOOL_ROUNDS):
            reply = log.track(llm.generate(system=system, messages=messages, timeout=deadline.remaining(), tools=TOOL_SPECS))
            if not reply.tool_calls:
                if not reply.text:
                    raise LLMUnavailable("empty reply")
                log.write("ok", deadline)
                return ChatResponse(answer=_tidy(reply.text), ai_generated=True, source="ai", tools_used=log.tools)
            messages.append(ModelMessage(reply))
            messages.append(ToolResultMessage([(call, run_tool(ctx, call)) for call in reply.tool_calls]))
            log.tools += [call.name for call in reply.tool_calls]
        raise LLMUnavailable("too many tool rounds")
    except LLMUnavailable as exc:
        log.write("fallback", deadline)
        answer = BUSY_FALLBACK if exc.busy else CHAT_FALLBACK
        return ChatResponse(answer=answer, ai_generated=False, source="fallback", tools_used=log.tools)


# Dashboard summary -------------------------------------------------------------------


class _Bullets(BaseModel):
    bullets: list[str] = Field(min_length=3, max_length=5)


BULLETS_SCHEMA = {
    "type": "object",
    "properties": {"bullets": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5}},
    "required": ["bullets"],
}


def summarize_dashboard(db: Client, llm: LLM | None, user: User) -> SummaryResponse:
    stats = dashboard_service.organization(db)
    kpis = stats.model_dump(mode="json", exclude={"recent_pending"})
    log = _Log(db, user, "summary", json.dumps(kpis))
    _enforce_rate_limit(log)
    deadline = _Deadline(get_settings().ai_timeout_seconds)
    try:
        if llm is None:
            raise LLMUnavailable("no AI key configured")
        result = _generate_json(
            llm, log, deadline, prompts.summary_prompt(), f"KPI JSON:\n{json.dumps(kpis)}", BULLETS_SCHEMA, _Bullets.model_validate
        )
        log.write("ok", deadline)
        return SummaryResponse(bullets=[_tidy(b) for b in result.bullets], ai_generated=True)
    except LLMUnavailable:
        log.write("fallback", deadline)
        return SummaryResponse(bullets=[], ai_generated=False, message=SUMMARY_FALLBACK)


# Smart leave -------------------------------------------------------------------------


class _RawLeaveDraft(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str = Field(min_length=1, max_length=500)


def draft_leave(db: Client, llm: LLM | None, user: User, text: str) -> LeaveDraftResponse:
    """Parse free text into a leave request draft. Never saves anything; the user confirms in the form."""
    log = _Log(db, user, "leave_draft", text)
    _enforce_rate_limit(log)
    deadline = _Deadline(get_settings().ai_timeout_seconds)
    leave_types = organization_service.list_leave_types(db)
    try:
        if llm is None or not leave_types:
            raise LLMUnavailable("no AI key configured or no leave types")
        today = company_today(get_company(db))
        by_name = {t.name.lower(): t for t in leave_types}
        schema = {
            "type": "object",
            "properties": {
                "leave_type": {"type": "string", "enum": [t.name for t in leave_types]},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "reason": {"type": "string"},
            },
            "required": ["leave_type", "start_date", "end_date", "reason"],
        }

        def parse(data: dict) -> LeaveDraft:
            raw = _RawLeaveDraft.model_validate(data)
            leave_type = by_name.get(raw.leave_type.strip().lower())
            if leave_type is None:
                raise ValueError(f"leave_type must be one of {', '.join(by_name)}")
            if raw.end_date < raw.start_date:
                raise ValueError("end_date is before start_date")
            if raw.start_date < today:
                raise ValueError("start_date is in the past")
            return LeaveDraft(
                leave_type_id=leave_type.id,
                leave_type_name=leave_type.name,
                start_date=raw.start_date,
                end_date=raw.end_date,
                reason=raw.reason.strip(),
            )

        draft = _generate_json(llm, log, deadline, prompts.leave_draft_prompt(today, leave_types), text, schema, parse)
        log.write("ok", deadline)
        return LeaveDraftResponse(draft=draft, ai_generated=True)
    except LLMUnavailable:
        log.write("fallback", deadline)
        return LeaveDraftResponse(draft=None, ai_generated=False, message=LEAVE_FALLBACK)
