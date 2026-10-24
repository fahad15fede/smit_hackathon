from fastapi import APIRouter, status

from ...schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from ...services import employees as employee_service
from ..deps import Db, ManagerUser

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeOut])
def list_employees(db: Db, _: ManagerUser):
    return employee_service.list_employees(db)


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Db, user: ManagerUser):
    return employee_service.create_employee(db, user, payload)


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: int, db: Db, _: ManagerUser):
    return employee_service.get_employee(db, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Db, user: ManagerUser):
    return employee_service.update_employee(db, user, employee_id, payload)
