import contextlib
import io
import json
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import create_user
from scripts.create_admin import create_or_promote_admin


db = SessionLocal()
results = {}

admin_email = "admin_script_test@example.com"
common_email = "common_script_test@example.com"
secret_password = "SenhaAdminSuperSecreta123"

try:
    db.query(User).filter(User.email.in_([admin_email, common_email])).delete(synchronize_session=False)
    db.commit()

    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        status_created, admin_id = create_or_promote_admin(
            db,
            name="Admin Script",
            email=admin_email,
            password=secret_password,
        )
    admin_count = db.query(User).filter(User.email == admin_email).count()
    admin_user = db.query(User).filter(User.email == admin_email).first()

    results["1_admin_created"] = status_created == "created"
    results["2_admin_role"] = admin_user is not None and admin_user.role == "admin"
    results["3_admin_active"] = admin_user is not None and admin_user.is_active is True
    results["4_no_duplicate_after_create"] = admin_count == 1
    results["5_password_not_printed_on_create"] = secret_password not in output.getvalue()

    status_exists, same_admin_id = create_or_promote_admin(
        db,
        name="Admin Script",
        email=admin_email,
        password=None,
    )
    admin_count_after_repeat = db.query(User).filter(User.email == admin_email).count()

    results["6_repeat_is_idempotent"] = status_exists == "exists" and same_admin_id == admin_id
    results["7_repeat_does_not_duplicate"] = admin_count_after_repeat == 1

    common_user = create_user(
        db,
        UserCreate(name="Common Script", email=common_email, password="senha123"),
    )
    status_promoted, promoted_id = create_or_promote_admin(
        db,
        name="Common Script",
        email=common_email,
        password=None,
    )
    db.refresh(common_user)

    results["8_existing_user_promoted"] = (
        status_promoted == "promoted"
        and promoted_id == common_user.id
        and common_user.role == "admin"
    )

    try:
        create_or_promote_admin(
            db,
            name="Invalid",
            email="not-an-email",
            password=secret_password,
        )
        results["9_invalid_email_fails"] = False
    except Exception:
        db.rollback()
        results["9_invalid_email_fails"] = True
finally:
    db.query(User).filter(User.email.in_([admin_email, common_email])).delete(synchronize_session=False)
    db.commit()
    db.close()

print(json.dumps(results, indent=2))
assert all(results.values()), results
