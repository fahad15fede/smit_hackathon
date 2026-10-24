"""Reference data: departments and leave types."""

from supabase import Client

from ..models import Department, LeaveType, User
from ..repositories import organization as organization_repo
from ..schemas.employee import DepartmentCreate
from ..schemas.leave import LeaveTypeCreate
from . import audit


def list_departments(db: Client) -> list[Department]:
    return organization_repo.list_departments(db)


def create_department(db: Client, actor: User, data: DepartmentCreate) -> Department:
    department = organization_repo.create_department(db, data.name.strip())
    audit.record(db, actor, "department.created", department.name)
    return department


def list_leave_types(db: Client) -> list[LeaveType]:
    return organization_repo.list_leave_types(db)


def create_leave_type(db: Client, actor: User, data: LeaveTypeCreate) -> LeaveType:
    leave_type = organization_repo.create_leave_type(db, data.name.strip(), data.annual_quota, data.is_paid)
    audit.record(db, actor, "leave_type.created", leave_type.name)
    return leave_type
