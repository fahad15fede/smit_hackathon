from fastapi import APIRouter, status

from ...schemas.company import CompanyOut, CompanyUpdate, HolidayCreate, HolidayOut
from ...schemas.employee import DepartmentCreate, DepartmentOut
from ...schemas.leave import LeaveTypeCreate, LeaveTypeOut
from ...services import company as company_service
from ...services import organization as organization_service
from ..deps import AdminUser, CurrentUser, Db

router = APIRouter(tags=["company"])


@router.get("/company", response_model=CompanyOut)
def get_company(db: Db, _: CurrentUser):
    return company_service.get_company(db)


@router.patch("/company", response_model=CompanyOut)
def update_company(payload: CompanyUpdate, db: Db, user: AdminUser):
    return company_service.update_company(db, user, payload)


@router.get("/holidays", response_model=list[HolidayOut])
def list_holidays(db: Db, _: CurrentUser):
    return company_service.list_holidays(db)


@router.post("/holidays", response_model=HolidayOut, status_code=status.HTTP_201_CREATED)
def add_holiday(payload: HolidayCreate, db: Db, user: AdminUser):
    return company_service.add_holiday(db, user, payload)


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(holiday_id: int, db: Db, user: AdminUser):
    company_service.delete_holiday(db, user, holiday_id)


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Db, _: CurrentUser):
    return organization_service.list_departments(db)


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def add_department(payload: DepartmentCreate, db: Db, user: AdminUser):
    return organization_service.create_department(db, user, payload)


@router.get("/leave-types", response_model=list[LeaveTypeOut])
def list_leave_types(db: Db, _: CurrentUser):
    return organization_service.list_leave_types(db)


@router.post("/leave-types", response_model=LeaveTypeOut, status_code=status.HTTP_201_CREATED)
def add_leave_type(payload: LeaveTypeCreate, db: Db, user: AdminUser):
    return organization_service.create_leave_type(db, user, payload)
