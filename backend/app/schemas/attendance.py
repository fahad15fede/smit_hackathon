from datetime import date, datetime

from pydantic import BaseModel

from ..models import AttendanceStatus
from .common import EmployeeBrief, ORMModel


class AttendanceOut(ORMModel):
    id: int
    day: date
    check_in: datetime
    check_out: datetime | None
    status: AttendanceStatus
    employee: EmployeeBrief


class AttendanceSummary(BaseModel):
    """Attendance over a date range. ``attendance_rate`` is check-ins / (headcount x working days), in percent."""

    start_date: date
    end_date: date
    working_days: int
    headcount: int
    check_ins: int
    on_time: int
    late: int
    attendance_rate: float | None
