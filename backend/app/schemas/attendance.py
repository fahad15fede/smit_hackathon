from datetime import date, datetime

from ..models import AttendanceStatus
from .common import EmployeeBrief, ORMModel


class AttendanceOut(ORMModel):
    id: int
    day: date
    check_in: datetime
    check_out: datetime | None
    status: AttendanceStatus
    employee: EmployeeBrief
