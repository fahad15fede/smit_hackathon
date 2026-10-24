from supabase import Client

from ..db.query import execute, first, payload
from ..models import Department, LeaveType


def list_departments(db: Client) -> list[Department]:
    return [Department.model_validate(row) for row in execute(db.table("departments").select("*").order("name"))]


def get_department(db: Client, department_id: int) -> Department | None:
    row = first(db.table("departments").select("*").eq("id", department_id))
    return Department.model_validate(row) if row else None


def create_department(db: Client, name: str) -> Department:
    query = db.table("departments").insert({"name": name})
    (row,) = execute(query, conflict="Department already exists")
    return Department.model_validate(row)


def list_leave_types(db: Client) -> list[LeaveType]:
    return [LeaveType.model_validate(row) for row in execute(db.table("leave_types").select("*").order("name"))]


def get_leave_type(db: Client, leave_type_id: int) -> LeaveType | None:
    row = first(db.table("leave_types").select("*").eq("id", leave_type_id))
    return LeaveType.model_validate(row) if row else None


def create_leave_type(db: Client, name: str, annual_quota: int, is_paid: bool) -> LeaveType:
    values = payload({"name": name, "annual_quota": annual_quota, "is_paid": is_paid})
    (row,) = execute(db.table("leave_types").insert(values), conflict="Leave type already exists")
    return LeaveType.model_validate(row)
