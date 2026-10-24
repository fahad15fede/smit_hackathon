from supabase import Client

from ..db.query import execute
from ..models import AuditLog


def record(db: Client, actor_id: int | None, action: str, detail: str) -> None:
    execute(db.table("audit_logs").insert({"actor_id": actor_id, "action": action, "detail": detail}))


def list_recent(db: Client, limit: int) -> list[AuditLog]:
    query = db.table("audit_logs").select("*, actor:users!actor_id(id,email)").order("id", desc=True).limit(limit)
    return [AuditLog.model_validate(row) for row in execute(query)]
