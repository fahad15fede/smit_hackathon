"""Role-scoped HR assistant.

The model only ever sees records the asking user is already allowed to view. When no Gemini
key is configured, or the call fails, a deterministic rule-based answer is returned instead.
"""

import logging

from supabase import Client

from ..core.config import get_settings
from ..models import Role, User
from ..schemas.audit import AskResponse
from . import attendance, audit, dashboard, leaves

logger = logging.getLogger(__name__)

GEMINI_TIMEOUT_MS = 15_000

SYSTEM_PROMPT = (
    "You are the HR assistant inside HCM Lite. Answer briefly and only from the HR context provided. "
    "If the context does not contain the answer, say so and suggest which HCM Lite page to check. "
    "Never invent employees, numbers, or policies."
)


def _organization_context(db: Client) -> tuple[str, dict]:
    stats = dashboard.organization(db)
    today = stats.today
    on_leave = [f"{item.employee.full_name} ({item.leave_type.name})" for item in leaves.on_leave(db, today)]
    late = [r.employee.full_name for r in attendance.list_records(db, start=today, end=today) if r.status == "late"]
    lines = [
        f"Date: {today} ({'working day' if stats.is_working_day else 'non-working day'})",
        f"Active employees: {stats.headcount}",
        f"Present on time: {stats.present}; late: {stats.late}; absent: {stats.absent}",
        f"On approved leave today: {', '.join(on_leave) or 'nobody'}",
        f"Late today: {', '.join(late) or 'nobody'}",
        f"Pending leave requests: {stats.pending_leaves}",
    ]
    facts = {"on_leave": on_leave, "late": late, "present": stats.present, "pending": stats.pending_leaves}
    return "\n".join(lines), facts


def _personal_context(db: Client, user: User) -> tuple[str, dict]:
    stats = dashboard.personal(db, user)
    record = stats.attendance
    attendance_line = (
        f"Checked in at {record.check_in:%H:%M} ({record.status})" if record else "Not checked in today"
    )
    balances = [f"{b.leave_type.name}: {b.remaining} remaining of {b.leave_type.annual_quota}" for b in stats.balances]
    payslip = stats.latest_payslip
    lines = [
        f"Employee: {user.employee.full_name}",
        f"Date: {stats.today}",
        f"Attendance today: {attendance_line}",
        f"Leave balances ({stats.today.year}): {'; '.join(balances) or 'no leave types configured'}",
        f"Pending leave requests: {stats.pending_leaves}",
        f"Latest payslip: {f'{payslip.month}, net {payslip.net:,.2f}' if payslip else 'none yet'}",
    ]
    facts = {"attendance": attendance_line, "balances": balances, "pending": stats.pending_leaves}
    return "\n".join(lines), facts


def _rule_based_answer(question: str, role: Role, facts: dict) -> str:
    text = question.lower()
    if role is Role.EMPLOYEE:
        if "balance" in text or "leave" in text:
            return "Your leave balances: " + ("; ".join(facts["balances"]) or "no leave types are configured yet.")
        if "attendance" in text or "check" in text:
            return facts["attendance"] + "."
        return "I can tell you about your attendance today and your leave balances."
    if "leave" in text:
        names = facts["on_leave"]
        return f"{len(names)} on leave today: {', '.join(names)}." if names else "Nobody is on approved leave today."
    if "late" in text:
        names = facts["late"]
        return f"{len(names)} late today: {', '.join(names)}." if names else "Nobody has checked in late today."
    if "attendance" in text or "present" in text:
        return f"{facts['present']} employees checked in on time today and {len(facts['late'])} were late."
    if "pending" in text or "approval" in text:
        return f"There are {facts['pending']} leave requests awaiting review."
    return "I can answer questions about today's attendance, late arrivals, leave and pending approvals."


def _ask_gemini(question: str, context: str) -> str | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS)
        )
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=f"HR context:\n{context}\n\nQuestion: {question}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
        )
        return (response.text or "").strip() or None
    except Exception:  # The assistant must never take the request down with it.
        logger.exception("Gemini request failed; falling back to rule-based answer")
        return None


def ask(db: Client, user: User, question: str) -> AskResponse:
    if user.role is Role.EMPLOYEE:
        context, facts = _personal_context(db, user)
    else:
        context, facts = _organization_context(db)

    answer = _ask_gemini(question, context)
    source = "gemini"
    if answer is None:
        answer, source = _rule_based_answer(question, user.role, facts), "rules"

    audit.record(db, user, "assistant.question", question)
    return AskResponse(answer=answer, source=source)
