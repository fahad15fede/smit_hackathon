"""Typed rows read from Supabase.

Each record mirrors a table in ``supabase/schema.sql``. Embedded relations (PostgREST
resource embedding) appear as nested records. Response schemas read these with
``from_attributes``, so computed ``@property`` values are serialized too.
"""

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from .enums import AttendanceStatus, LeaveStatus, PayrollStatus, Role


class Record(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Company(Record):
    id: int
    name: str
    timezone: str
    office_start: time
    grace_minutes: int
    weekend_days: str  # comma-separated lowercase weekday names

    @property
    def weekend(self) -> set[str]:
        return {day.strip().lower() for day in self.weekend_days.split(",") if day.strip()}


class Holiday(Record):
    id: int
    name: str
    day: date


class Department(Record):
    id: int
    name: str


class EmployeeRef(Record):
    """The slice of an employee embedded in other records."""

    id: int
    full_name: str
    designation: str


class Employee(Record):
    id: int
    full_name: str
    email: str
    phone: str | None = None
    address: str | None = None
    department_id: int | None = None
    designation: str
    join_date: date
    monthly_salary: Decimal
    is_active: bool
    department: Department | None = None
    role: Role | None = None  # filled from the linked user account


class User(Record):
    id: int
    email: str
    password_hash: str
    role: Role
    is_active: bool
    employee_id: int
    employee: Employee


class LeaveType(Record):
    id: int
    name: str
    annual_quota: int
    is_paid: bool


class Attendance(Record):
    id: int
    employee_id: int
    day: date
    check_in: datetime
    check_out: datetime | None = None
    status: AttendanceStatus
    employee: EmployeeRef


class LeaveRequest(Record):
    id: int
    employee_id: int
    leave_type_id: int
    start_date: date
    end_date: date
    working_days: int
    reason: str
    status: LeaveStatus
    reviewed_by_id: int | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None
    created_at: datetime
    employee: EmployeeRef
    leave_type: LeaveType


class PayrollRunRef(Record):
    month: str
    status: PayrollStatus


class Payslip(Record):
    id: int
    payroll_run_id: int
    employee_id: int
    working_days: int
    unpaid_days: int
    gross: Decimal
    deduction: Decimal
    net: Decimal
    employee: EmployeeRef
    payroll_run: PayrollRunRef

    @property
    def month(self) -> str:
        return self.payroll_run.month

    @property
    def status(self) -> PayrollStatus:
        return self.payroll_run.status


class PayrollRun(Record):
    id: int
    month: str  # YYYY-MM
    status: PayrollStatus
    created_by_id: int | None = None
    finalized_at: datetime | None = None
    created_at: datetime
    payslips: list[Payslip] = []

    @property
    def employee_count(self) -> int:
        return len(self.payslips)

    @property
    def total_gross(self) -> Decimal:
        return sum((slip.gross for slip in self.payslips), Decimal("0"))

    @property
    def total_deduction(self) -> Decimal:
        return sum((slip.deduction for slip in self.payslips), Decimal("0"))

    @property
    def total_net(self) -> Decimal:
        return sum((slip.net for slip in self.payslips), Decimal("0"))


class AuditActor(Record):
    id: int
    email: str


class AuditLog(Record):
    id: int
    action: str
    detail: str
    created_at: datetime
    actor: AuditActor | None = None
