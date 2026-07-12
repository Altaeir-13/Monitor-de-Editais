import json
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-config-import-123456")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from pydantic import ValidationError

from app.core.config import Settings


VALID_REMOTE = {
    "DATABASE_URL": "postgresql://postgres:validpassword123@db:5432/monitor_editais",
    "SECRET_KEY": "valid-remote-secret-key-with-more-than-32-characters",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "ENVIRONMENT": "staging",
    "API_ROOT_PATH": "/api/",
    "OPENAPI_ENABLED": False,
    "UVICORN_WORKERS": 1,
    "BACKEND_CORS_ORIGINS": ["https://staging.example.net"],
    "CRAWLER_SCHEDULER_ENABLED": False,
    "CRAWLER_INTERVAL_MINUTES": 360,
}


def create_settings(**overrides):
    values = {**VALID_REMOTE, **overrides}
    return Settings(_env_file=None, **values)


def is_rejected(**overrides) -> bool:
    try:
        create_settings(**overrides)
    except ValidationError:
        return True
    return False


settings = create_settings()
results = {
    "1_postgres_component_fields_not_required": not hasattr(settings, "POSTGRES_PASSWORD"),
    "2_root_path_normalized": settings.API_ROOT_PATH == "/api",
    "3_openapi_configurable": settings.OPENAPI_ENABLED is False,
    "4_secret_placeholder_rejected": is_rejected(SECRET_KEY="change-me"),
    "5_database_placeholder_rejected": is_rejected(
        DATABASE_URL="postgresql://postgres:change-me@db:5432/monitor_editais"
    ),
    "6_sqlite_remote_rejected": is_rejected(DATABASE_URL="sqlite:///app.db"),
    "7_wildcard_cors_rejected": is_rejected(BACKEND_CORS_ORIGINS=["*"]),
    "8_http_cors_rejected": is_rejected(BACKEND_CORS_ORIGINS=["http://staging.example.net"]),
    "9_scheduler_multiple_workers_rejected": is_rejected(
        CRAWLER_SCHEDULER_ENABLED=True,
        UVICORN_WORKERS=2,
    ),
    "10_invalid_interval_rejected": is_rejected(CRAWLER_INTERVAL_MINUTES=0),
}

print(json.dumps(results, indent=2))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
