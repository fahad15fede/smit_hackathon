from datetime import date

from fastapi import APIRouter

from ...schemas.attendance import AttendanceOut
from ...services import attendance as attendance_service
from ..deps import CurrentUser, Db, ManagerUser

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/check-in", response_model=AttendanceOut)
def check_in(db: Db, user: CurrentUser):
    return attendance_service.check_in(db, user)


@router.post("/check-out", response_model=AttendanceOut)
def check_out(db: Db, user: CurrentUser):
    return attendance_service.check_out(db, user)


@router.get("/me", response_model=list[AttendanceOut])
def my_attendance(db: Db, user: CurrentUser, start: date | None = None, end: date | None = None):
    return attendance_service.list_records(db, employee_id=user.employee_id, start=start, end=end)


@router.get("", response_model=list[AttendanceOut])
def all_attendance(
    db: Db,
    _: ManagerUser,
    start: date | None = None,
    end: date | None = None,
    employee_id: int | None = None,
):
    return attendance_service.list_records(db, employee_id=employee_id, start=start, end=end)
