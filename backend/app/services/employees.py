from supabase import Client

from ..core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from ..core.security import hash_password
from ..models import Employee, Role, User
from ..repositories import organization as organization_repo
from ..repositories import people as people_repo
from ..schemas.employee import EmployeeCreate, EmployeeUpdate
from . import audit


def list_employees(db: Client) -> list[Employee]:
    return people_repo.list_employees(db)


def get_employee(db: Client, employee_id: int) -> Employee:
    employee = people_repo.get_employee(db, employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")
    return employee


def _ensure_department(db: Client, department_id: int | None) -> None:
    if department_id is not None and organization_repo.get_department(db, department_id) is None:
        raise NotFoundError("Department not found")


def create_employee(db: Client, actor: User, data: EmployeeCreate) -> Employee:
    """Register an employee and their login account."""
    if data.role is not Role.EMPLOYEE and actor.role is not Role.ADMIN:
        raise PermissionDeniedError("Only an Admin can create HR or Admin accounts")
    email = data.email.lower()
    if people_repo.email_in_use(db, email):
        raise ConflictError("An account with this email already exists")
    _ensure_department(db, data.department_id)

    values = {**data.model_dump(exclude={"email", "password", "role"}), "email": email, "is_active": True}
    employee = people_repo.create_employee(db, values)
    try:
        people_repo.create_user(
            db, email=email, password_hash=hash_password(data.password), role=data.role, employee_id=employee.id
        )
    except Exception:
        people_repo.delete_employee(db, employee.id)  # no orphaned profile without an account
        raise

    audit.record(db, actor, "employee.created", f"{email} ({data.role})")
    return get_employee(db, employee.id)


def update_employee(db: Client, actor: User, employee_id: int, data: EmployeeUpdate) -> Employee:
    employee = get_employee(db, employee_id)
    if employee.role is Role.ADMIN and actor.role is not Role.ADMIN:
        raise PermissionDeniedError("Only an Admin can edit an Admin profile")
    if employee.id == actor.employee_id and data.is_active is False:
        raise PermissionDeniedError("You cannot deactivate your own account")

    changes = data.model_dump(exclude_unset=True)
    if "department_id" in changes:
        _ensure_department(db, changes["department_id"])
    if changes:
        people_repo.update_employee(db, employee_id, changes)
    if "is_active" in changes:
        people_repo.update_user_for_employee(db, employee_id, {"is_active": changes["is_active"]})

    audit.record(db, actor, "employee.updated", f"{employee.email}: {', '.join(changes) or 'no changes'}")
    return get_employee(db, employee_id)
