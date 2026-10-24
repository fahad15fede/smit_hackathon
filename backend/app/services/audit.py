from supabase import Client

from ..models import AuditLog, User
from ..repositories import audit as audit_repo


def record(db: Client, actor: User | None, action: str, detail: str) -> None:
    audit_repo.record(db, actor.id if actor else None, action, detail)


def list_recent(db: Client, limit: int = 100) -> list[AuditLog]:
    return audit_repo.list_recent(db, limit)
