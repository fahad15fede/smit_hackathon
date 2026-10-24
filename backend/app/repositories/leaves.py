from datetime import date

from supabase import Client

from ..db.query import Row, execute, first, payload
from ..models import LeaveRequest, LeaveStatus

LEAVE_SELECT = (
    "*, employee:employees!employee_id(id,full_name,designation), leave_type:leave_types!leave_type_id(*)"
)


def list_requests(db: Client, *, employee_id: int | None = None, status: LeaveStatus | None = None) -> list[LeaveRequest]:
    query = db.table("leave_requests").select(LEAVE_SELECT)
    if employee_id is not None:
        query = query.eq("employee_id", employee_id)
    if status is not None:
        query = query.eq("status", status.value)
    query = query.order("created_at", desc=True).order("id", desc=True)
    return [LeaveRequest.model_validate(row) for row in execute(query)]


def get(db: Client, leave_id: int) -> LeaveRequest | None:
    row = first(db.table("leave_requests").select(LEAVE_SELECT).eq("id", leave_id))
    return LeaveRequest.model_validate(row) if row else None


def create(db: Client, values: Row) -> LeaveRequest:
    (row,) = execute(db.table("leave_requests").insert(payload(values)))
    return get(db, row["id"])


def update(db: Client, leave_id: int, changes: Row) -> LeaveRequest:
    execute(db.table("leave_requests").update(payload(changes)).eq("id", leave_id))
    return get(db, leave_id)


def days_taken(db: Client, employee_id: int, leave_type_id: int, year: int, status: LeaveStatus) -> int:
    query = (
        db.table("leave_requests")
        .select("working_days")
        .eq("employee_id", employee_id)
        .eq("leave_type_id", leave_type_id)
        .eq("status", status.value)
        .gte("start_date", date(year, 1, 1).isoformat())
        .lte("start_date", date(year, 12, 31).isoformat())
    )
    return sum(row["working_days"] for row in execute(query))


def has_overlap(db: Client, employee_id: int, start: date, end: date, statuses: tuple[LeaveStatus, ...]) -> bool:
    query = (
        db.table("leave_requests")
        .select("id")
        .eq("employee_id", employee_id)
        .in_("status", [status.value for status in statuses])
        .lte("start_date", end.isoformat())
        .gte("end_date", start.isoformat())
    )
    return first(query) is not None


def approved_overlapping(db: Client, start: date, end: date) -> list[LeaveRequest]:
    query = (
        db.table("leave_requests")
        .select(LEAVE_SELECT)
        .eq("status", LeaveStatus.APPROVED.value)
        .lte("start_date", end.isoformat())
        .gte("end_date", start.isoformat())
    )
    return [LeaveRequest.model_validate(row) for row in execute(query)]


def count_pending(db: Client, employee_id: int) -> int:
    query = db.table("leave_requests").select("id").eq("employee_id", employee_id).eq("status", LeaveStatus.PENDING.value)
    return len(execute(query))
