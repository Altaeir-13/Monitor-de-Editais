import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

test_db_path = Path(tempfile.gettempdir()) / f"monitor_editais_health_{uuid4().hex}.db"
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{test_db_path.as_posix()}",
        "SECRET_KEY": "test-secret-key-for-health-tests-12345678",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "OPENAPI_ENABLED": "true",
        "CRAWLER_SCHEDULER_ENABLED": "false",
    }
)

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import main as main_module
from app.db.base import Base
from app.db.session import engine


Base.metadata.create_all(bind=engine)
results: dict[str, bool] = {}

try:
    with TestClient(main_module.app) as client:
        health_response = client.get("/health")
        results["1_health_status"] = health_response.status_code == 200
        results["2_health_body"] = health_response.json() == {"status": "ok"}

        ready_response = client.get("/ready")
        results["3_ready_status"] = ready_response.status_code == 200
        results["4_ready_body"] = ready_response.json() == {"status": "ok"}

        openapi_response = client.get("/openapi.json")
        openapi_payload = openapi_response.json()
        results["5_openapi_status"] = openapi_response.status_code == 200
        results["6_health_documented"] = "/health" in openapi_payload.get("paths", {})
        results["7_ready_documented"] = "/ready" in openapi_payload.get("paths", {})

        original_engine = main_module.engine

        class FailingEngine:
            def connect(self):
                raise SQLAlchemyError("simulated database outage")

        try:
            main_module.engine = FailingEngine()
            failed_ready_response = client.get("/ready")
        finally:
            main_module.engine = original_engine

        results["8_ready_failure_status"] = failed_ready_response.status_code == 503
        results["9_ready_failure_body"] = failed_ready_response.json() == {
            "detail": {"status": "error"}
        }
finally:
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
