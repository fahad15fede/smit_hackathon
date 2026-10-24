from datetime import datetime

from supabase import Client

from ..db.query import execute


def record(
    db: Client,
    *,
    user_id: int,
    feature: str,
    prompt: str,
    tools_called: list[str],
    status: str,
    latency_ms: int,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    execute(
        db.table("ai_logs").insert(
            {
                "user_id": user_id,
                "feature": feature,
                "prompt": prompt[:2000],
                "tools_called": ",".join(tools_called),
                "status": status,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }
        )
    )


def count_since(db: Client, user_id: int, since: datetime) -> int:
    """Requests that reached the AI pipeline (rate-limited attempts are not counted)."""
    query = (
        db.table("ai_logs")
        .select("id")
        .eq("user_id", user_id)
        .neq("status", "rate_limited")
        .gte("created_at", since.isoformat())
    )
    return len(execute(query))
