import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

test_db_path = Path(tempfile.gettempdir()) / f"monitor_editais_auth_{uuid4().hex}.db"
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{test_db_path.as_posix()}",
        "SECRET_KEY": "test-secret-key-for-auth-tests-123456789",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CRAWLER_SCHEDULER_ENABLED": "false",
    }
)

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User
from main import app


Base.metadata.create_all(bind=engine)
results: dict[str, bool] = {}
db = SessionLocal()

try:
    with TestClient(app) as client:
        payload = {
            "name": "Teste Usuario",
            "email": "teste@example.com",
            "password": "SenhaForte123",
        }

        register_response = client.post("/auth/register", json=payload)
        results["1_register"] = (
            register_response.status_code == 200
            and register_response.json().get("email") == payload["email"]
        )

        duplicate_response = client.post("/auth/register", json=payload)
        results["2_register_duplicate"] = duplicate_response.status_code == 400

        login_response = client.post(
            "/auth/login",
            data={"username": payload["email"], "password": payload["password"]},
        )
        login_payload = login_response.json() if login_response.status_code == 200 else {}
        token = login_payload.get("access_token")
        results["3_login"] = login_response.status_code == 200 and bool(token)

        wrong_password_response = client.post(
            "/auth/login",
            data={"username": payload["email"], "password": "SenhaErrada"},
        )
        results["4_login_wrong_password"] = wrong_password_response.status_code in {400, 401}

        me_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        results["5_me_with_token"] = (
            me_response.status_code == 200
            and me_response.json().get("email") == payload["email"]
        )

        no_token_response = client.get("/users/me")
        results["6_me_without_token"] = no_token_response.status_code == 401

        user_in_db = db.query(User).filter(User.email == payload["email"]).first()
        results["7_db_user_exists"] = user_in_db is not None
        results["8_password_is_hashed"] = (
            user_in_db is not None and user_in_db.password_hash != payload["password"]
        )
finally:
    db.query(User).filter(User.email == "teste@example.com").delete(synchronize_session=False)
    db.commit()
    db.close()
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
