from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from ..models import LeaveStatus
from .common import EmployeeBrief, ORMModel


class LeaveTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    annual_quota: int = Field(ge=0, le=365)
    is_paid: bool = True


class LeaveTypeOut(ORMModel):
    id: int
    name: str
    annual_quota: int
    is_paid: bool


class LeaveCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def check_range(self) -> "LeaveCreate":
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        if self.start_date.year != self.end_date.year:
            raise ValueError("A leave request cannot span two calendar years")
        return self


class LeaveDecision(BaseModel):
    approved: bool
    comment: str | None = Field(default=None, max_length=500)


class LeaveOut(ORMModel):
    id: int
    start_date: date
    end_date: date
    working_days: int
    reason: str
    status: LeaveStatus
    review_comment: str | None
    reviewed_at: datetime | None
    created_at: datetime
    employee: EmployeeBrief
    leave_type: LeaveTypeOut


class LeaveBalanceOut(BaseModel):
    leave_type: LeaveTypeOut
    year: int
    used: int
    pending: int
    remaining: int
