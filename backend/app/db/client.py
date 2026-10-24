"""Supabase client used for all data access (PostgREST over HTTPS)."""

from functools import lru_cache

from supabase import Client, ClientOptions, create_client

from ..core.config import get_settings

REQUEST_TIMEOUT_SECONDS = 15


@lru_cache
def get_client() -> Client:
    settings = get_settings()
    options = ClientOptions(postgrest_client_timeout=REQUEST_TIMEOUT_SECONDS, auto_refresh_token=False, persist_session=False)
    return create_client(settings.supabase_url, settings.supabase_secret_key, options=options)


def get_db() -> Client:
    """FastAPI dependency; overridden with an in-memory fake in tests."""
    return get_client()
