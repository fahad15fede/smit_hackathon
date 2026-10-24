from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from ..models import Role
from .auth import PASSWORD_CONSTRAINTS
from .common import ORMModel

SALARY_CONSTRAINTS = {"ge": 0, "max_digits": 12, "decimal_places": 2}


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class DepartmentOut(ORMModel):
    id: int
    name: str


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    designation: str = Field(min_length=2, max_length=100)
    join_date: date
    monthly_salary: Decimal = Field(**SALARY_CONSTRAINTS)
    department_id: int | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    role: Role = Role.EMPLOYEE
    password: str = Field(**PASSWORD_CONSTRAINTS)


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    designation: str | None = Field(default=None, min_length=2, max_length=100)
    monthly_salary: Decimal | None = Field(default=None, **SALARY_CONSTRAINTS)
    department_id: int | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class EmployeeOut(ORMModel):
    id: int
    full_name: str
    email: str
    designation: str
    join_date: date
    monthly_salary: float
    phone: str | None
    address: str | None
    is_active: bool
    department: DepartmentOut | None
    role: Role
