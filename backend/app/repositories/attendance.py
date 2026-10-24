from datetime import date, datetime

from supabase import Client

from ..db.query import Row, execute, first, payload
from ..models import Attendance, AttendanceStatus

ATTENDANCE_SELECT = "*, employee:employees!employee_id(id,full_name,designation)"


def get(db: Client, employee_id: int, day: date) -> Attendance | None:
    query = db.table("attendance").select(ATTENDANCE_SELECT).eq("employee_id", employee_id).eq("day", day.isoformat())
    row = first(query)
    return Attendance.model_validate(row) if row else None


def create(db: Client, employee_id: int, day: date, check_in: datetime, status: AttendanceStatus) -> Attendance:
    values = payload({"employee_id": employee_id, "day": day, "check_in": check_in, "status": status})
    execute(db.table("attendance").insert(values), conflict="You have already checked in today")
    return get(db, employee_id, day)


def set_check_out(db: Client, record_id: int, check_out: datetime) -> None:
    execute(db.table("attendance").update(payload({"check_out": check_out})).eq("id", record_id))


def list_records(
    db: Client, *, employee_id: int | None = None, start: date | None = None, end: date | None = None, limit: int = 500
) -> list[Attendance]:
    query = db.table("attendance").select(ATTENDANCE_SELECT)
    if employee_id is not None:
        query = query.eq("employee_id", employee_id)
    if start is not None:
        query = query.gte("day", start.isoformat())
    if end is not None:
        query = query.lte("day", end.isoformat())
    query = query.order("day", desc=True).order("check_in", desc=True).limit(limit)
    return [Attendance.model_validate(row) for row in execute(query)]


def days_between(db: Client, start: date, end: date) -> list[Row]:
    """Lightweight ``{employee_id, day, status}`` rows for aggregation."""
    query = db.table("attendance").select("employee_id,day,status").gte("day", start.isoformat()).lte("day", end.isoformat())
    return [
        {"employee_id": row["employee_id"], "day": date.fromisoformat(row["day"]), "status": AttendanceStatus(row["status"])}
        for row in execute(query)
    ]
