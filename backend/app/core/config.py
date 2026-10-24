"""Application settings, loaded from environment variables and ``backend/.env``."""

import base64
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
DEFAULT_JWT_SECRET = "development-only-secret-change-me-in-production"
API_KEYS_HINT = "Supabase -> Project Settings -> API Keys"


def _legacy_key_role(key: str) -> str | None:
    """Return the ``role`` claim of a legacy JWT-style Supabase key (``anon`` / ``service_role``)."""
    try:
        payload = key.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return claims.get("role")
    except (IndexError, ValueError):
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,  # a blank `KEY=` line in .env falls back to the default
        extra="ignore",
    )

    app_name: str = "HCM Lite API"
    environment: Literal["development", "production"] = "development"

    # Supabase -> Project Settings -> Data API -> Project URL, e.g. https://<project-ref>.supabase.co
    supabase_url: str = Field(default="", validate_default=True)
    # Server-side key that bypasses Row Level Security. Never expose it to the browser.
    supabase_secret_key: str = Field(
        default="",
        validate_default=True,
        validation_alias=AliasChoices("SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    )

    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    # Comma-separated list of origins allowed to call the API.
    frontend_origin: str = "http://localhost:5173"

    # Hosted LLM for the assistant: Groq (OpenAI-compatible API). Backend-only; the browser never sees it.
    ai_api_key: str | None = Field(default=None, validation_alias=AliasChoices("AI_API_KEY", "GROQ_API_KEY"))
    ai_model: str = Field(default="openai/gpt-oss-120b", validation_alias=AliasChoices("AI_MODEL", "GROQ_MODEL"))
    ai_base_url: str = "https://api.groq.com/openai/v1"
    # Cap per model reply. For reasoning models it covers hidden reasoning plus the answer.
    ai_max_output_tokens: int = 1500
    # Reasoning models only (openai/gpt-oss-*): "low" keeps answers fast and leaves room for the reply.
    ai_reasoning_effort: Literal["low", "medium", "high"] = "low"
    ai_timeout_seconds: float = 15
    ai_requests_per_hour: int = 20

    @field_validator("supabase_url")
    @classmethod
    def check_supabase_url(cls, url: str) -> str:
        url = url.strip().rstrip("/")
        if not url:
            raise ValueError(f"SUPABASE_URL is not set. Add your Project URL to {ENV_FILE} (Supabase -> Project Settings -> Data API).")
        if not url.startswith(("https://", "http://")):
            raise ValueError("SUPABASE_URL must be the Project URL (https://<project-ref>.supabase.co), not a Postgres connection string")
        return url

    @field_validator("supabase_secret_key")
    @classmethod
    def check_secret_key(cls, key: str) -> str:
        key = key.strip()
        if not key:
            raise ValueError(f"SUPABASE_SECRET_KEY is not set. Add the secret key to {ENV_FILE} ({API_KEYS_HINT}).")
        if key.startswith("sb_publishable_") or _legacy_key_role(key) == "anon":
            raise ValueError(
                "SUPABASE_SECRET_KEY is a publishable/anon key. The backend needs the secret key "
                f"(sb_secret_..., or the legacy service_role key) from {API_KEYS_HINT}."
            )
        return key

    @model_validator(mode="after")
    def reject_insecure_production(self) -> "Settings":
        if self.environment == "production" and self.jwt_secret == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET must be set in production")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
