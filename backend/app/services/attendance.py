from datetime import date, datetime, timedelta

from supabase import Client

from ..core.exceptions import BusinessRuleError, ConflictError
from ..models import Attendance, AttendanceStatus, Employee, User
from ..repositories import attendance as attendance_repo
from ..repositories import people as people_repo
from ..schemas.attendance import AttendanceSummary
from . import audit
from .calendar import WorkCalendar, company_now, company_today
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


def summary(db: Client, start: date, end: date, *, employee_id: int | None = None) -> AttendanceSummary:
    """Attendance totals for the organization, or for one employee when ``employee_id`` is given.

    Days after today are ignored, so a month-to-date rate is not diluted by future days.
    """
    company = get_company(db)
    end = min(end, company_today(company))
    working_days = WorkCalendar(db, company, start, end).working_days(start, end) if start <= end else []
    rows = [
        row
        for row in attendance_repo.days_between(db, start, end)
        if employee_id is None or row["employee_id"] == employee_id
    ]
    headcount = 1 if employee_id is not None else people_repo.count_active(db)
    late = sum(row["status"] is AttendanceStatus.LATE for row in rows)
    expected = headcount * len(working_days)
    return AttendanceSummary(
        start_date=start,
        end_date=end,
        working_days=len(working_days),
        headcount=headcount,
        check_ins=len(rows),
        on_time=len(rows) - late,
        late=late,
        attendance_rate=round(100 * len(rows) / expected, 1) if expected else None,
    )


def late_ranking(db: Client, start: date, end: date) -> list[tuple[Employee, int]]:
    """Employees ordered by number of late check-ins in the range (most first)."""
    counts: dict[int, int] = {}
    for row in attendance_repo.days_between(db, start, end):
        if row["status"] is AttendanceStatus.LATE:
            counts[row["employee_id"]] = counts.get(row["employee_id"], 0) + 1
    employees = {employee.id: employee for employee in people_repo.list_employees(db)}
    ranking = [(employees[employee_id], count) for employee_id, count in counts.items() if employee_id in employees]
    return sorted(ranking, key=lambda item: (-item[1], item[0].full_name))
