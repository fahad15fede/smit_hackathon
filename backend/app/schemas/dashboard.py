from datetime import date

from pydantic import BaseModel

from .attendance import AttendanceOut
from .leave import LeaveBalanceOut, LeaveOut
from .payroll import PayslipOut


class AttendanceTrendPoint(BaseModel):
    day: date
    present: int
    late: int


class OrganizationDashboard(BaseModel):
    today: date
    is_working_day: bool
    headcount: int
    present: int
    late: int
    on_leave: int
    absent: int
    pending_leaves: int
    month_attendance_rate: float | None
    trend: list[AttendanceTrendPoint]
    recent_pending: list[LeaveOut]


class PersonalDashboard(BaseModel):
    today: date
    is_working_day: bool
    attendance: AttendanceOut | None
    balances: list[LeaveBalanceOut]
    pending_leaves: int
    latest_payslip: PayslipOut | None
