from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REMOTE_ENVIRONMENTS = {"staging", "production"}
INSECURE_MARKERS = ("change-me", "changeme", "replace-me", "example-secret")


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    API_ROOT_PATH: str = ""
    OPENAPI_ENABLED: bool = True
    LOG_LEVEL: Literal["critical", "error", "warning", "info", "debug", "trace"] = "info"
    UVICORN_WORKERS: int = Field(default=1, ge=1)
    FORWARDED_ALLOW_IPS: str = "127.0.0.1"

    # SMTP configuration
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""

    # CORS configuration
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Crawler scheduler
    CRAWLER_SCHEDULER_ENABLED: bool = False
    CRAWLER_INTERVAL_MINUTES: int = Field(default=360, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("API_ROOT_PATH")
    @classmethod
    def normalize_api_root_path(cls, value: str) -> str:
        value = value.strip()
        if value in {"", "/"}:
            return ""
        if not value.startswith("/"):
            raise ValueError("API_ROOT_PATH must start with '/'.")
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.CRAWLER_SCHEDULER_ENABLED and self.UVICORN_WORKERS != 1:
            raise ValueError("CRAWLER_SCHEDULER_ENABLED=true requires UVICORN_WORKERS=1.")

        if self.ENVIRONMENT not in REMOTE_ENVIRONMENTS:
            return self

        secret_key = self.SECRET_KEY.strip()
        lowered_secret = secret_key.lower()
        if len(secret_key) < 32 or any(marker in lowered_secret for marker in INSECURE_MARKERS):
            raise ValueError("SECRET_KEY must be a non-placeholder value with at least 32 characters.")

        database_url = self.DATABASE_URL.strip()
        lowered_database_url = database_url.lower()
        if not lowered_database_url.startswith(("postgresql://", "postgresql+")):
            raise ValueError("DATABASE_URL must use PostgreSQL in staging and production.")
        if any(marker in lowered_database_url for marker in INSECURE_MARKERS):
            raise ValueError("DATABASE_URL contains an insecure placeholder.")

        if not self.API_ROOT_PATH:
            raise ValueError("API_ROOT_PATH is required in staging and production.")

        if not self.BACKEND_CORS_ORIGINS:
            raise ValueError("BACKEND_CORS_ORIGINS must be explicit in staging and production.")
        for origin in self.BACKEND_CORS_ORIGINS:
            if origin == "*" or not origin.startswith("https://"):
                raise ValueError("Remote CORS origins must be explicit HTTPS origins.")

        return self


settings = Settings()
