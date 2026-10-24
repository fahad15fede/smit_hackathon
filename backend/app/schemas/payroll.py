from datetime import datetime

from pydantic import BaseModel, Field

from ..models import PayrollStatus
from .common import EmployeeBrief, ORMModel


class PayrollCreate(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-10"])


class PayrollRunOut(ORMModel):
    id: int
    month: str
    status: PayrollStatus
    created_at: datetime
    finalized_at: datetime | None
    employee_count: int
    total_gross: float
    total_deduction: float
    total_net: float


class PayslipOut(ORMModel):
    id: int
    month: str
    status: PayrollStatus
    working_days: int
    unpaid_days: int
    gross: float
    deduction: float
    net: float
    employee: EmployeeBrief


class PayrollRunDetail(PayrollRunOut):
    payslips: list[PayslipOut]
