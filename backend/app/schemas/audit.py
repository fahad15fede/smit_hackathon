from datetime import datetime

from .common import ORMModel


class AuditActor(ORMModel):
    id: int
    email: str


class AuditLogOut(ORMModel):
    id: int
    action: str
    detail: str
    created_at: datetime
    actor: AuditActor | None
