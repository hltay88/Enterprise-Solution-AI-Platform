"""Environment-based application settings."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Project Atlas API"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str = "postgresql://atlas:atlas@db:5432/atlas"
    secret_key: str = "change-me-in-local-dev"
    jwt_expire_minutes: int = 60

    demo_user_email: str = "demo@example.com"
    demo_user_password: str = "changeme"
    demo_user_name: str = "Atlas Demo"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    # google-genai also accepts GOOGLE_API_KEY; keep as optional alias.
    google_api_key: str | None = None
    gemini_model: str = "gemini-flash-latest"
    # auto | gemini | openai | local
    atlas_ai_provider: str = "auto"

    @field_validator("openai_api_key", "gemini_api_key", "google_api_key", mode="before")
    @classmethod
    def sanitize_api_keys(cls, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().strip('"').strip("'").strip()
        return cleaned or None

    @property
    def effective_gemini_api_key(self) -> str | None:
        return self.gemini_api_key or self.google_api_key

    @field_validator("openai_model", mode="before")
    @classmethod
    def sanitize_openai_model(cls, value: object) -> str:
        if value is None:
            return "gpt-4o-mini"
        cleaned = str(value).strip().strip('"').strip("'").strip()
        return cleaned or "gpt-4o-mini"

    @field_validator("gemini_model", mode="before")
    @classmethod
    def sanitize_gemini_model(cls, value: object) -> str:
        if value is None:
            return "gemini-flash-latest"
        cleaned = str(value).strip().strip('"').strip("'").strip()
        return cleaned or "gemini-flash-latest"

    @field_validator("atlas_ai_provider", mode="before")
    @classmethod
    def sanitize_atlas_ai_provider(cls, value: object) -> str:
        allowed = {"auto", "gemini", "openai", "local"}
        cleaned = str(value or "auto").strip().strip('"').strip("'").strip().lower()
        return cleaned if cleaned in allowed else "auto"

    storage_path: str = "/app/storage/uploads"
    libreoffice_path: str = "soffice"
    # Sprint 1 sync upload default; Phase 2 /api/v1 enforces ATLAS-027 (50 MB) separately.
    max_upload_mb: int = 50
    max_batch_upload_mb: int = 200

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
