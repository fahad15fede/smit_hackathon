from datetime import date, datetime, timedelta

from supabase import Client

from ..core.exceptions import BusinessRuleError, ConflictError
from ..models import Attendance, AttendanceStatus, User
from ..repositories import attendance as attendance_repo
from . import audit
from .calendar import WorkCalendar, company_now
from .company import get_company


def get_record(db: Client, employee_id: int, day: date) -> Attendance | None:
    return attendance_repo.get(db, employee_id, day)


def check_in(db: Client, user: User) -> Attendance:
    """Record today's check-in using the server clock in the company's timezone."""
    company = get_company(db)
    now = company_now(company)
    today = now.date()
    if not WorkCalendar(db, company, today, today).is_working_day(today):
        raise BusinessRuleError("Today is not a working day")
    if attendance_repo.get(db, user.employee_id, today):
        raise ConflictError("You have already checked in today")

    late_after = datetime.combine(today, company.office_start, now.tzinfo) + timedelta(minutes=company.grace_minutes)
    status = AttendanceStatus.LATE if now > late_after else AttendanceStatus.PRESENT
    record = attendance_repo.create(db, user.employee_id, today, now, status)
    audit.record(db, user, "attendance.check_in", f"{today} ({status})")
    return record


def check_out(db: Client, user: User) -> Attendance:
    company = get_company(db)
    now = company_now(company)
    record = attendance_repo.get(db, user.employee_id, now.date())
    if record is None:
        raise BusinessRuleError("Check in before checking out")
    if record.check_out is not None:
        raise ConflictError("You have already checked out today")
    attendance_repo.set_check_out(db, record.id, now)
    audit.record(db, user, "attendance.check_out", str(record.day))
    return record.model_copy(update={"check_out": now})


def list_records(
    db: Client, *, employee_id: int | None = None, start: date | None = None, end: date | None = None
) -> list[Attendance]:
    return attendance_repo.list_records(db, employee_id=employee_id, start=start, end=end)
