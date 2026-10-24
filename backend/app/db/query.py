"""Executes PostgREST queries and translates database failures into domain errors."""

import logging
from typing import Any

import httpx
from postgrest.exceptions import APIError
from pydantic_core import to_jsonable_python

from ..core.exceptions import BusinessRuleError, ConflictError, DatabaseUnavailableError

logger = logging.getLogger(__name__)

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
MISSING_TABLE_CODES = {"42P01", "PGRST205"}

Row = dict[str, Any]


def execute(query: Any, *, conflict: str | None = None) -> list[Row]:
    """Run ``query`` and return its rows.

    ``conflict`` is the user-facing message for a unique-constraint violation.
    """
    try:
        response = query.execute()
    except APIError as exc:
        if exc.code == UNIQUE_VIOLATION:
            raise ConflictError(conflict or "This record already exists") from exc
        if exc.code == FOREIGN_KEY_VIOLATION:
            raise BusinessRuleError("This record is linked to other data and cannot be changed") from exc
        if exc.code in MISSING_TABLE_CODES:
            raise DatabaseUnavailableError(
                "Database tables are missing. Run supabase/schema.sql in the Supabase SQL Editor."
            ) from exc
        logger.error("Supabase query failed: %r", exc)
        raise DatabaseUnavailableError(f"Database error: {exc.message or exc.code or 'unknown error'}") from exc
    except httpx.HTTPError as exc:
        logger.error("Cannot reach Supabase: %s", exc)
        raise DatabaseUnavailableError("Cannot reach Supabase. Check SUPABASE_URL and your network.") from exc
    return response.data or []


def payload(values: Any) -> Any:
    """Convert dates, decimals and enums into JSON values PostgREST accepts."""
    return to_jsonable_python(values)


def first(query: Any) -> Row | None:
    rows = execute(query.limit(1))
    return rows[0] if rows else None
