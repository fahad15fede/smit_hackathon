from fastapi import APIRouter, status

from ...schemas.payroll import PayrollCreate, PayrollRunDetail, PayrollRunOut, PayslipOut
from ...services import payroll as payroll_service
from ..deps import AdminUser, CurrentUser, Db, HRUser, ManagerUser

router = APIRouter(tags=["payroll"])


@router.get("/payroll", response_model=list[PayrollRunOut])
def list_runs(db: Db, _: ManagerUser):
    return payroll_service.list_runs(db)


@router.post("/payroll", response_model=PayrollRunDetail, status_code=status.HTTP_201_CREATED)
def create_run(payload: PayrollCreate, db: Db, user: HRUser):
    return payroll_service.create_run(db, user, payload.month)


@router.get("/payroll/{run_id}", response_model=PayrollRunDetail)
def get_run(run_id: int, db: Db, _: ManagerUser):
    return payroll_service.get_run(db, run_id)


@router.post("/payroll/{run_id}/finalize", response_model=PayrollRunOut)
def finalize_run(run_id: int, db: Db, user: AdminUser):
    return payroll_service.finalize_run(db, user, run_id)


@router.delete("/payroll/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(run_id: int, db: Db, user: HRUser):
    payroll_service.delete_draft(db, user, run_id)


@router.get("/payslips/me", response_model=list[PayslipOut])
def my_payslips(db: Db, user: CurrentUser):
    return payroll_service.payslips_for(db, user.employee_id)
