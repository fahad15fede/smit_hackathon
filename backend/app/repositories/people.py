"""Employees and their login accounts (``employees`` and ``users`` tables)."""

from datetime import date

from supabase import Client

from ..db.query import Row, execute, first, payload
from ..models import Employee, Role, User

EMPLOYEE_SELECT = "*, department:departments!department_id(id,name)"
USER_SELECT = "*, employee:employees!employee_id(*)"


def _with_roles(db: Client, rows: list[Row]) -> list[Employee]:
    """Attach each employee's account role (stored on ``users``)."""
    ids = [row["id"] for row in rows]
    roles = {}
    if ids:
        accounts = execute(db.table("users").select("employee_id,role").in_("employee_id", ids))
        roles = {account["employee_id"]: account["role"] for account in accounts}
    return [Employee.model_validate({**row, "role": roles.get(row["id"])}) for row in rows]


def list_employees(db: Client) -> list[Employee]:
    return _with_roles(db, execute(db.table("employees").select(EMPLOYEE_SELECT).order("full_name")))


def get_employee(db: Client, employee_id: int) -> Employee | None:
    rows = execute(db.table("employees").select(EMPLOYEE_SELECT).eq("id", employee_id))
    return _with_roles(db, rows)[0] if rows else None


def list_payable(db: Client, joined_by: date) -> list[Employee]:
    """Active employees with a salary who had joined by ``joined_by``."""
    query = (
        db.table("employees")
        .select("*")
        .eq("is_active", True)
        .gt("monthly_salary", 0)
        .lte("join_date", joined_by.isoformat())
    )
    return [Employee.model_validate(row) for row in execute(query)]


def count_active(db: Client) -> int:
    return len(execute(db.table("employees").select("id").eq("is_active", True)))


def email_in_use(db: Client, email: str) -> bool:
    return bool(
        first(db.table("users").select("id").eq("email", email))
        or first(db.table("employees").select("id").eq("email", email))
    )


def create_employee(db: Client, values: Row) -> Employee:
    query = db.table("employees").insert(payload(values))
    (row,) = execute(query, conflict="An account with this email already exists")
    return Employee.model_validate(row)


def update_employee(db: Client, employee_id: int, changes: Row) -> None:
    execute(db.table("employees").update(payload(changes)).eq("id", employee_id))


def delete_employee(db: Client, employee_id: int) -> None:
    execute(db.table("employees").delete().eq("id", employee_id))


def get_user(db: Client, user_id: int) -> User | None:
    row = first(db.table("users").select(USER_SELECT).eq("id", user_id))
    return User.model_validate(row) if row else None


def find_user_by_email(db: Client, email: str) -> User | None:
    row = first(db.table("users").select(USER_SELECT).eq("email", email))
    return User.model_validate(row) if row else None


def create_user(db: Client, *, email: str, password_hash: str, role: Role, employee_id: int) -> User:
    values = payload(
        {"email": email, "password_hash": password_hash, "role": role, "is_active": True, "employee_id": employee_id}
    )
    (row,) = execute(db.table("users").insert(values), conflict="An account with this email already exists")
    return get_user(db, row["id"])  # re-read to embed the employee profile


def update_user(db: Client, user_id: int, changes: Row) -> None:
    execute(db.table("users").update(payload(changes)).eq("id", user_id))


def update_user_for_employee(db: Client, employee_id: int, changes: Row) -> None:
    execute(db.table("users").update(payload(changes)).eq("employee_id", employee_id))
