from fastapi import APIRouter, Query

from ...schemas.audit import AskRequest, AskResponse, AuditLogOut
from ...schemas.dashboard import OrganizationDashboard, PersonalDashboard
from ...services import assistant as assistant_service
from ...services import audit as audit_service
from ...services import dashboard as dashboard_service
from ..deps import AdminUser, CurrentUser, Db, ManagerUser

router = APIRouter(tags=["insights"])


@router.get("/dashboard/organization", response_model=OrganizationDashboard)
def organization_dashboard(db: Db, _: ManagerUser):
    return dashboard_service.organization(db)


@router.get("/dashboard/me", response_model=PersonalDashboard)
def personal_dashboard(db: Db, user: CurrentUser):
    return dashboard_service.personal(db, user)


@router.get("/audit", response_model=list[AuditLogOut])
def audit_log(db: Db, _: AdminUser, limit: int = Query(default=100, ge=1, le=500)):
    return audit_service.list_recent(db, limit)


@router.post("/assistant/ask", response_model=AskResponse)
def ask_assistant(payload: AskRequest, db: Db, user: CurrentUser):
    return assistant_service.ask(db, user, payload.question)
