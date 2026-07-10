import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def remove_sqlite_files(db_path: Path) -> None:
    for path in [db_path, db_path.with_suffix(db_path.suffix + "-wal"), db_path.with_suffix(db_path.suffix + "-shm")]:
        path.unlink(missing_ok=True)


def run_test() -> dict[str, object]:
    temp_dir = Path(tempfile.gettempdir())
    db_path = temp_dir / f"monitor_editais_sqlite_compat_{uuid.uuid4().hex}.db"
    app_db_path = backend_path / "app.db"

    assert db_path.resolve() != app_db_path.resolve(), "O teste não deve usar backend/app.db"

    os.environ["POSTGRES_USER"] = "sqlite_compat"
    os.environ["POSTGRES_PASSWORD"] = "sqlite_compat"
    os.environ["POSTGRES_DB"] = "monitor_editais_sqlite_compat"
    os.environ["DATABASE_URL"] = sqlite_url(db_path)
    os.environ["SECRET_KEY"] = "sqlite-compat-test-secret"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["CRAWLER_SCHEDULER_ENABLED"] = "false"

    try:
        alembic_cfg = Config(str(backend_path / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")

        engine = create_engine(sqlite_url(db_path), pool_pre_ping=True)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        from app.schemas.user import UserCreate
        from app.services.user import authenticate_user, create_user

        db = TestingSessionLocal()
        try:
            email = f"sqlite_compat_{uuid.uuid4().hex}@example.com"
            user = create_user(
                db,
                UserCreate(
                    name="SQLite Compat",
                    email=email,
                    password="senha123",
                ),
            )

            assert user.id is not None, "O id do usuário deveria ser preenchido"
            assert user.created_at is not None, "created_at deveria ser preenchido pelo banco"

            persisted_user = authenticate_user(db, email=email, password="senha123")
            assert persisted_user is not None, "A autenticação deveria funcionar com a senha criada"
            assert persisted_user.id == user.id, "O usuário autenticado deveria ser o usuário criado"

            persisted_user.name = "SQLite Compat Atualizado"
            db.commit()
            db.refresh(persisted_user)
            assert persisted_user.updated_at is not None, "updated_at deveria ser preenchido ao atualizar"

            return {
                "sqlite_database": str(db_path),
                "user_persisted": True,
                "user_id": user.id,
                "created_at_set": user.created_at is not None,
                "authentication_ok": True,
                "update_ok": True,
                "updated_at_set": persisted_user.updated_at is not None,
            }
        finally:
            db.close()
            engine.dispose()
    finally:
        remove_sqlite_files(db_path)


if __name__ == "__main__":
    print(json.dumps(run_test(), indent=2, default=str))