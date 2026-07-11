import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.db.session import SessionLocal
from app.schemas.user import UserCreate
from app.services.user import create_user, get_user_by_email


def create_or_promote_admin(
    db: Session,
    *,
    name: str,
    email: str,
    password: Optional[str],
) -> tuple[str, int]:
    existing_user = get_user_by_email(db, email=email)

    if existing_user:
        changed = False
        if existing_user.role != "admin":
            existing_user.role = "admin"
            changed = True
        if not existing_user.is_active:
            existing_user.is_active = True
            changed = True

        if changed:
            db.commit()
            return "promoted", existing_user.id
        return "exists", existing_user.id

    if not password:
        raise ValueError("ADMIN_PASSWORD is required when creating a new admin.")

    user_in = UserCreate(name=name, email=email, password=password)
    user = create_user(db, user_in)
    user.role = "admin"
    db.commit()
    db.refresh(user)
    return "created", user.id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or promote an admin user.")
    parser.add_argument("--name", default=os.getenv("ADMIN_NAME", "Administrador"))
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"), required=os.getenv("ADMIN_EMAIL") is None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    password = os.getenv("ADMIN_PASSWORD")

    db = SessionLocal()
    try:
        existing_user = get_user_by_email(db, email=args.email)
        if existing_user is None and password is None:
            password = getpass.getpass("Admin password: ")

        status, user_id = create_or_promote_admin(
            db,
            name=args.name,
            email=args.email,
            password=password,
        )
    except (ValidationError, ValueError) as exc:
        db.rollback()
        print(f"Admin creation failed: {exc}", file=sys.stderr)
        return 2
    except SQLAlchemyError:
        db.rollback()
        print("Admin creation failed because of a database error. Check backend logs.", file=sys.stderr)
        return 1
    except Exception:
        db.rollback()
        print("Admin creation failed because of an unexpected error. Check backend logs.", file=sys.stderr)
        return 1
    finally:
        db.close()

    messages = {
        "created": "Admin user created.",
        "promoted": "Existing user promoted to admin.",
        "exists": "Admin user already exists.",
    }
    print(f"{messages[status]} user_id={user_id} email={args.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
