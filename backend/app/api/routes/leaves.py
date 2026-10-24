from fastapi import APIRouter, Query, status

from ...models import LeaveStatus
from ...schemas.leave import LeaveBalanceOut, LeaveCreate, LeaveDecision, LeaveOut
from ...services import leaves as leave_service
from ..deps import CurrentUser, Db, ManagerUser

router = APIRouter(prefix="/leaves", tags=["leaves"])


@router.get("/me", response_model=list[LeaveOut])
def my_leaves(db: Db, user: CurrentUser):
    return leave_service.list_requests(db, employee_id=user.employee_id)


@router.get("/me/balances", response_model=list[LeaveBalanceOut])
def my_balances(db: Db, user: CurrentUser, year: int | None = None):
    return leave_service.balances(db, user.employee_id, year)


@router.get("", response_model=list[LeaveOut])
def all_leaves(db: Db, _: ManagerUser, status_filter: LeaveStatus | None = Query(None, alias="status")):
    return leave_service.list_requests(db, status=status_filter)


@router.post("", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
def request_leave(payload: LeaveCreate, db: Db, user: CurrentUser):
    return leave_service.create_request(db, user, payload)


@router.post("/{leave_id}/decision", response_model=LeaveOut)
def decide_leave(leave_id: int, payload: LeaveDecision, db: Db, user: ManagerUser):
    return leave_service.decide(db, user, leave_id, payload)


@router.post("/{leave_id}/cancel", response_model=LeaveOut)
def cancel_leave(leave_id: int, db: Db, user: CurrentUser):
    return leave_service.cancel(db, user, leave_id)
