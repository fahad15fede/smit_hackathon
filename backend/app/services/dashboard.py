from collections import Counter
from datetime import timedelta

from supabase import Client

from ..models import AttendanceStatus, LeaveStatus, User
from ..repositories import attendance as attendance_repo
from ..repositories import leaves as leave_repo
from ..repositories import people as people_repo
from ..schemas.attendance import AttendanceOut
from ..schemas.dashboard import AttendanceTrendPoint, OrganizationDashboard, PersonalDashboard
from ..schemas.leave import LeaveOut
from ..schemas.payroll import PayslipOut
from . import attendance, leaves, payroll
from .calendar import WorkCalendar, company_today, iter_days
from .company import get_company

TREND_DAYS = 14


def organization(db: Client) -> OrganizationDashboard:
    company = get_company(db)
    today = company_today(company)
    trend_start = today - timedelta(days=TREND_DAYS - 1)
    is_working_day = WorkCalendar(db, company, today, today).is_working_day(today)

    counts = Counter((row["day"], row["status"]) for row in attendance_repo.days_between(db, trend_start, today))
    trend = [
        AttendanceTrendPoint(
            day=day,
            present=counts.get((day, AttendanceStatus.PRESENT), 0),
            late=counts.get((day, AttendanceStatus.LATE), 0),
        )
        for day in iter_days(trend_start, today)
    ]

    headcount = people_repo.count_active(db)
    present, late = trend[-1].present, trend[-1].late
    on_leave = len(leaves.on_leave(db, today))
    pending = leaves.list_requests(db, status=LeaveStatus.PENDING)

    return OrganizationDashboard(
        today=today,
        is_working_day=is_working_day,
        headcount=headcount,
        present=present,
        late=late,
        on_leave=on_leave,
        absent=max(0, headcount - present - late - on_leave) if is_working_day else 0,
        pending_leaves=len(pending),
        month_attendance_rate=attendance.summary(db, today.replace(day=1), today).attendance_rate,
        trend=trend,
        recent_pending=[LeaveOut.model_validate(item) for item in pending[:5]],
    )


def personal(db: Client, user: User) -> PersonalDashboard:
    company = get_company(db)
    today = company_today(company)
    record = attendance.get_record(db, user.employee_id, today)
    payslips = payroll.payslips_for(db, user.employee_id)
    pending = leave_repo.count_pending(db, user.employee_id)
    return PersonalDashboard(
        today=today,
        is_working_day=WorkCalendar(db, company, today, today).is_working_day(today),
        attendance=AttendanceOut.model_validate(record) if record else None,
        balances=leaves.balances(db, user.employee_id, today.year),
        pending_leaves=pending,
        latest_payslip=PayslipOut.model_validate(payslips[0]) if payslips else None,
    )
