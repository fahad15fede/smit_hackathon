"""Tools the assistant model may call.

Every tool runs with the asking user's scope and reuses the same services and role rules as
the REST API: org-wide data is for Admin/HR only, employees only ever see their own records.
Tools are read-only. Errors are returned to the model as data so it can explain them.
"""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from supabase import Client

from ..core.exceptions import AppError
from ..models import Company, LeaveStatus, Role, User
from ..services import attendance as attendance_service
from ..services import employees as employee_service
from ..services import leaves as leave_service
from ..services import organization as organization_service
from ..services import payroll as payroll_service
from .llm import ToolCall, ToolSpec

MANAGERS = frozenset({Role.ADMIN, Role.HR})
NOT_PERMITTED = {
    "error": "not_permitted",
    "message": "This information is not available to the user's role. Politely refuse.",
}


@dataclass
class ToolContext:
    db: Client
    user: User
    company: Company
    today: date

    @property
    def is_manager(self) -> bool:
        return self.user.role in MANAGERS


@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    handler: Callable[[ToolContext, dict[str, Any]], dict[str, Any]]
    roles: frozenset[Role] | None = None  # None: every role (handler scopes the data)


# Argument helpers -------------------------------------------------------------------

DATE_RANGE = {
    "start_date": {"type": "string", "description": "ISO date (YYYY-MM-DD). Defaults to the 1st of the current month."},
    "end_date": {"type": "string", "description": "ISO date (YYYY-MM-DD). Defaults to today."},
}


def _period(ctx: ToolContext, args: dict[str, Any]) -> tuple[date, date]:
    start = date.fromisoformat(args["start_date"]) if args.get("start_date") else ctx.today.replace(day=1)
    end = date.fromisoformat(args["end_date"]) if args.get("end_date") else ctx.today
    if end < start:
        raise ValueError("end_date is before start_date")
    return start, end


def _matches(value: str | None, needle: str | None) -> bool:
    return not needle or (value or "").lower().find(needle.strip().lower()) >= 0


def _money(value: Any) -> float:
    return round(float(value), 2)


# Handlers ---------------------------------------------------------------------------


NO_DEPARTMENT = "No department"


def _resolve_department(ctx: ToolContext, name: str) -> tuple[str | None, list[str]]:
    """Match a department by exact name, else by a unique partial match ("eng" -> "Engineering")."""
    names = [d.name for d in organization_service.list_departments(ctx.db)]
    wanted = name.strip().lower()
    exact = [n for n in names if n.lower() == wanted]
    partial = [n for n in names if wanted in n.lower()]
    match = exact or (partial if len(partial) == 1 else [])
    return (match[0] if match else None), names


def get_headcount(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    active = [e for e in employee_service.list_employees(ctx.db) if e.is_active]
    counts = Counter(e.department.name if e.department else NO_DEPARTMENT for e in active)
    departments = [d.name for d in organization_service.list_departments(ctx.db)]

    if args.get("department"):
        match, names = _resolve_department(ctx, args["department"])
        if match is None:
            return {"error": f"No department matches '{args['department']}'", "existing_departments": names}
        return {"department": match, "active_employees": counts.get(match, 0)}

    return {
        "active_employees": len(active),
        # Every department in the company, including ones with no employees yet.
        "by_department": {name: counts.get(name, 0) for name in departments},
        "without_department": counts.get(NO_DEPARTMENT, 0),
        "note": "without_department counts active people not assigned to any department (e.g. the Admin account).",
    }


def get_attendance_summary(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    start, end = _period(ctx, args)
    employee_id = None if ctx.is_manager else ctx.user.employee_id
    summary = attendance_service.summary(ctx.db, start, end, employee_id=employee_id)
    return {
        "scope": "organization" if employee_id is None else "you",
        **summary.model_dump(mode="json"),
        "expected_check_ins": summary.headcount * summary.working_days,
        "attendance_rate_definition": "check_ins / expected_check_ins, as a percent",
    }


def get_late_comers(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    start, end = _period(ctx, args)
    limit = max(1, min(int(args.get("limit") or 5), 20))
    ranking = attendance_service.late_ranking(ctx.db, start, end)
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "late_comers": [
            {"name": e.full_name, "designation": e.designation, "late_days": count} for e, count in ranking[:limit]
        ],
    }


def get_leave_summary(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    day = date.fromisoformat(args["date"]) if args.get("date") else ctx.today
    if ctx.is_manager:
        on_leave = leave_service.on_leave(ctx.db, day)
        pending = leave_service.list_requests(ctx.db, status=LeaveStatus.PENDING)
        return {
            "date": day.isoformat(),
            "on_leave_count": len(on_leave),
            "on_leave": [
                {"name": r.employee.full_name, "leave_type": r.leave_type.name, "until": r.end_date.isoformat()}
                for r in on_leave
            ],
            "pending_requests": len(pending),
        }
    mine = leave_service.list_requests(ctx.db, employee_id=ctx.user.employee_id)
    return {
        "scope": "you",
        "requests_by_status": dict(Counter(str(r.status) for r in mine)),
        "upcoming_approved": [
            {"leave_type": r.leave_type.name, "start_date": r.start_date.isoformat(), "end_date": r.end_date.isoformat()}
            for r in mine
            if r.status is LeaveStatus.APPROVED and r.end_date >= ctx.today
        ],
    }


def get_my_leave_balance(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    year = int(args.get("year") or ctx.today.year)
    balances = leave_service.balances(ctx.db, ctx.user.employee_id, year)
    wanted = [b for b in balances if _matches(b.leave_type.name, args.get("leave_type"))]
    return {
        "year": year,
        "note": None if wanted or not args.get("leave_type") else "No leave type matched; showing all.",
        "balances": [
            {
                "leave_type": b.leave_type.name,
                "paid": b.leave_type.is_paid,
                "annual_quota": b.leave_type.annual_quota,
                "used_approved": b.used,
                "pending": b.pending,
                "remaining": b.remaining,
            }
            for b in (wanted or balances)
        ],
    }


def get_payroll_summary(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    month = args.get("month")
    if not ctx.is_manager:
        slips = [s for s in payroll_service.payslips_for(ctx.db, ctx.user.employee_id) if not month or s.month == month]
        return {
            "scope": "your finalized payslips only",
            "payslips": [
                {"month": s.month, "gross": _money(s.gross), "deduction": _money(s.deduction), "net": _money(s.net), "unpaid_days": s.unpaid_days}
                for s in slips[:6]
            ],
        }
    runs = [r for r in payroll_service.list_runs(ctx.db) if not month or r.month == month]
    return {
        "currency": "PKR",
        "runs": [
            {
                "month": r.month,
                "status": str(r.status),
                "employees": r.employee_count,
                "total_gross": _money(r.total_gross),
                "total_deductions": _money(r.total_deduction),
                "total_net": _money(r.total_net),
            }
            for r in runs[:6]
        ],
    }


def search_employees(ctx: ToolContext, args: dict[str, Any]) -> dict[str, Any]:
    query, department = args.get("query"), args.get("department")
    if department:
        match, names = _resolve_department(ctx, department)
        if match is None:
            return {"error": f"No department matches '{department}'", "existing_departments": names}
        department = match
    found = [
        e
        for e in employee_service.list_employees(ctx.db)
        if (_matches(e.full_name, query) or _matches(e.email, query) or _matches(e.designation, query))
        and (not department or (e.department is not None and e.department.name == department))
    ]
    return {
        "count": len(found),
        "employees": [
            {
                "name": e.full_name,
                "email": e.email,
                "designation": e.designation,
                "department": e.department.name if e.department else None,
                "role": str(e.role),
                "active": e.is_active,
                "monthly_salary_pkr": _money(e.monthly_salary),
            }
            for e in found[:15]
        ],
    }


# Registry ---------------------------------------------------------------------------


def _tool(name: str, description: str, handler, properties: dict | None = None, roles=None) -> Tool:
    # Every parameter is optional, and models often send null for one they skip; strict providers
    # (e.g. Groq) reject null unless the schema allows it, so each type also admits null.
    nullable = {key: {**spec, "type": [spec["type"], "null"]} for key, spec in (properties or {}).items()}
    schema = {"type": "object", "properties": nullable}
    return Tool(ToolSpec(name, description, schema), handler, roles)


TOOLS: dict[str, Tool] = {
    tool.spec.name: tool
    for tool in [
        _tool(
            "get_headcount",
            "Number of active employees: the total, every department (including departments with zero "
            "employees) and how many have no department. Pass department for a single department. Admin/HR only.",
            get_headcount,
            {"department": {"type": "string", "description": "Optional department name"}},
            MANAGERS,
        ),
        _tool(
            "get_attendance_summary",
            "Check-ins, on-time vs late and the attendance rate for a date range (default: this month to date). "
            "Admin/HR get organization totals; employees get their own.",
            get_attendance_summary,
            DATE_RANGE,
        ),
        _tool(
            "get_late_comers",
            "Employees ranked by number of late check-ins in a date range (default: this month). For 'today', pass "
            "today's date as both start_date and end_date. Admin/HR only.",
            get_late_comers,
            {**DATE_RANGE, "limit": {"type": "integer", "description": "How many to return (default 5)"}},
            MANAGERS,
        ),
        _tool(
            "get_leave_summary",
            "Admin/HR: who is on approved leave on a date (default today) and the pending request count. "
            "Employees: a summary of their own leave requests.",
            get_leave_summary,
            {"date": {"type": "string", "description": "ISO date (YYYY-MM-DD). Defaults to today."}},
        ),
        _tool(
            "get_my_leave_balance",
            "The asking user's own leave balances (quota, used, pending, remaining) for a year.",
            get_my_leave_balance,
            {
                "leave_type": {"type": "string", "description": "Optional leave type name, e.g. 'Sick'"},
                "year": {"type": "integer", "description": "Defaults to the current year"},
            },
        ),
        _tool(
            "get_payroll_summary",
            "Admin/HR: payroll run totals and status. Employees: only their own finalized payslips.",
            get_payroll_summary,
            {"month": {"type": "string", "description": "Optional month as YYYY-MM"}},
        ),
        _tool(
            "search_employees",
            "Find employees by name, email or designation, optionally within a department; with no arguments it "
            "lists everyone. Admin/HR only.",
            search_employees,
            {
                "query": {"type": "string", "description": "Name, email or designation text"},
                "department": {"type": "string", "description": "Optional department name"},
            },
            MANAGERS,
        ),
    ]
}

TOOL_SPECS: list[ToolSpec] = [tool.spec for tool in TOOLS.values()]


def run_tool(ctx: ToolContext, call: ToolCall) -> dict[str, Any]:
    tool = TOOLS.get(call.name)
    if tool is None:
        return {"error": f"Unknown tool '{call.name}'"}
    if tool.roles is not None and ctx.user.role not in tool.roles:
        return NOT_PERMITTED
    try:
        return tool.handler(ctx, call.args)
    except AppError as exc:
        return {"error": exc.message}
    except (ValueError, TypeError, KeyError) as exc:
        return {"error": f"Invalid arguments: {exc}"}
