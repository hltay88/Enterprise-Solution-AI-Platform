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
    # auto | openai | local — auto uses local fallback when OpenAI quota/auth fails
    atlas_ai_provider: str = "auto"

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def sanitize_openai_api_key(cls, value: object) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip().strip('"').strip("'").strip()
        return cleaned or None

    @field_validator("openai_model", mode="before")
    @classmethod
    def sanitize_openai_model(cls, value: object) -> str:
        if value is None:
            return "gpt-4o-mini"
        cleaned = str(value).strip().strip('"').strip("'").strip()
        return cleaned or "gpt-4o-mini"

    @field_validator("atlas_ai_provider", mode="before")
    @classmethod
    def sanitize_atlas_ai_provider(cls, value: object) -> str:
        allowed = {"auto", "openai", "local"}
        cleaned = str(value or "auto").strip().strip('"').strip("'").strip().lower()
        return cleaned if cleaned in allowed else "auto"

    storage_path: str = "/app/storage/uploads"
    max_upload_mb: int = 10

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
