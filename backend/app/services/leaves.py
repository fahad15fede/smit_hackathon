from datetime import date, datetime, timezone

from supabase import Client

from ..core.exceptions import BusinessRuleError, ConflictError, NotFoundError, PermissionDeniedError
from ..models import LeaveRequest, LeaveStatus, LeaveType, User
from ..repositories import leaves as leave_repo
from ..repositories import organization as organization_repo
from ..schemas.leave import LeaveBalanceOut, LeaveCreate, LeaveDecision, LeaveTypeOut
from . import audit
from .calendar import WorkCalendar, company_today
from .company import get_company

ACTIVE_STATUSES = (LeaveStatus.PENDING, LeaveStatus.APPROVED)


def list_requests(db: Client, *, employee_id: int | None = None, status: LeaveStatus | None = None) -> list[LeaveRequest]:
    return leave_repo.list_requests(db, employee_id=employee_id, status=status)


def balance_for(db: Client, employee_id: int, leave_type: LeaveType, year: int) -> LeaveBalanceOut:
    used = leave_repo.days_taken(db, employee_id, leave_type.id, year, LeaveStatus.APPROVED)
    pending = leave_repo.days_taken(db, employee_id, leave_type.id, year, LeaveStatus.PENDING)
    return LeaveBalanceOut(
        leave_type=LeaveTypeOut.model_validate(leave_type),
        year=year,
        used=used,
        pending=pending,
        remaining=leave_type.annual_quota - used - pending,
    )


def balances(db: Client, employee_id: int, year: int | None = None) -> list[LeaveBalanceOut]:
    year = year or company_today(get_company(db)).year
    return [balance_for(db, employee_id, leave_type, year) for leave_type in organization_repo.list_leave_types(db)]


def create_request(db: Client, user: User, data: LeaveCreate) -> LeaveRequest:
    leave_type = organization_repo.get_leave_type(db, data.leave_type_id)
    if leave_type is None:
        raise NotFoundError("Leave type not found")
    if leave_repo.has_overlap(db, user.employee_id, data.start_date, data.end_date, ACTIVE_STATUSES):
        raise ConflictError("These dates overlap an existing leave request")

    calendar = WorkCalendar(db, get_company(db), data.start_date, data.end_date)
    days = len(calendar.working_days(data.start_date, data.end_date))
    if days == 0:
        raise BusinessRuleError("The selected dates contain no working days")
    if days > balance_for(db, user.employee_id, leave_type, data.start_date.year).remaining:
        raise BusinessRuleError(f"Insufficient {leave_type.name} balance")

    request = leave_repo.create(
        db,
        {**data.model_dump(), "employee_id": user.employee_id, "working_days": days, "status": LeaveStatus.PENDING},
    )
    audit.record(db, user, "leave.requested", f"#{request.id} {leave_type.name}, {days} day(s)")
    return request


def _get_pending(db: Client, leave_id: int) -> LeaveRequest:
    request = leave_repo.get(db, leave_id)
    if request is None:
        raise NotFoundError("Leave request not found")
    if request.status is not LeaveStatus.PENDING:
        raise ConflictError("This leave request has already been decided")
    return request


def decide(db: Client, reviewer: User, leave_id: int, decision: LeaveDecision) -> LeaveRequest:
    request = _get_pending(db, leave_id)
    if request.employee_id == reviewer.employee_id:
        raise PermissionDeniedError("You cannot review your own leave request")
    status = LeaveStatus.APPROVED if decision.approved else LeaveStatus.REJECTED
    updated = leave_repo.update(
        db,
        leave_id,
        {
            "status": status,
            "review_comment": decision.comment,
            "reviewed_by_id": reviewer.id,
            "reviewed_at": datetime.now(timezone.utc),
        },
    )
    audit.record(db, reviewer, f"leave.{status}", f"#{leave_id} for {request.employee.full_name}")
    return updated


def cancel(db: Client, user: User, leave_id: int) -> LeaveRequest:
    request = _get_pending(db, leave_id)
    if request.employee_id != user.employee_id:
        raise PermissionDeniedError("You can only cancel your own leave requests")
    updated = leave_repo.update(db, leave_id, {"status": LeaveStatus.CANCELLED})
    audit.record(db, user, "leave.cancelled", f"#{leave_id}")
    return updated


def on_leave(db: Client, day: date) -> list[LeaveRequest]:
    return leave_repo.approved_overlapping(db, day, day)
