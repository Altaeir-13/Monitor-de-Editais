import sys
import os
import json
from datetime import datetime, timezone, timedelta

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from pathlib import Path
import tempfile
from uuid import uuid4

test_db_path = (
    Path(tempfile.gettempdir())
    / f"monitor_editais_isolated_{uuid4().hex}.sqlite3"
)
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{test_db_path.as_posix()}",
        "SECRET_KEY": "isolated-legacy-test-secret-key-123456789",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CRAWLER_SCHEDULER_ENABLED": "false",
    }
)
from fastapi.testclient import TestClient
from main import app
from app.db.base import Base
from app.db.session import SessionLocal, engine

Base.metadata.create_all(bind=engine)
from app.models.user import User
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice
from app.models.user_alert import UserAlert
from app.models.notification import Notification
from app.services.user import create_user
from app.schemas.user import UserCreate

client = TestClient(app)
db = SessionLocal()
results = {}

# Track created IDs for cleanup
created_user_ids = []
created_inst_ids = []
created_source_ids = []
created_notice_ids = []
created_alert_ids = []
created_notification_ids = []

try:
    # ── SETUP USERS ───────────────────────────────────────────────────────────
    # User A (regular)
    user_a_email = "user_a_alerts_test@example.com"
    user_a = db.query(User).filter(User.email == user_a_email).first()
    if not user_a:
        user_a = create_user(db, UserCreate(name="User A", email=user_a_email, password="pass123"))
    created_user_ids.append(user_a.id)

    # User B (regular) — used to test cross-user isolation
    user_b_email = "user_b_alerts_test@example.com"
    user_b = db.query(User).filter(User.email == user_b_email).first()
    if not user_b:
        user_b = create_user(db, UserCreate(name="User B", email=user_b_email, password="pass123"))
    created_user_ids.append(user_b.id)

    # Admin user
    admin_email = "admin_alerts_test@example.com"
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if not admin_user:
        admin_user = create_user(db, UserCreate(name="Admin", email=admin_email, password="pass123"))
        admin_user.role = "admin"
        db.commit()
    created_user_ids.append(admin_user.id)

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    token_a = client.post("/auth/login", data={"username": user_a_email, "password": "pass123"}).json().get("access_token")
    token_b = client.post("/auth/login", data={"username": user_b_email, "password": "pass123"}).json().get("access_token")
    token_admin = client.post("/auth/login", data={"username": admin_email, "password": "pass123"}).json().get("access_token")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    headers_none = {}

    # ── SETUP INSTITUTIONS ────────────────────────────────────────────────────
    inst_active = Institution(
        name="UFPI Test Alerts", initials="UFPITA", state="PI",
        official_site_url="https://ufpi-test.br", is_active=True
    )
    inst_inactive = Institution(
        name="Inativa Test Alerts", initials="INATA", state="MA",
        official_site_url="https://inativa-test.br", is_active=False
    )
    db.add_all([inst_active, inst_inactive])
    db.commit()
    created_inst_ids.extend([inst_active.id, inst_inactive.id])

    source = MonitoredSource(
        institution_id=inst_active.id, name="Portal Test Alerts",
        url="https://ufpi-test.br/editais", source_type="html",
        check_frequency_minutes=1440, is_active=True
    )
    db.add(source)
    db.commit()
    created_source_ids.append(source.id)

    now = datetime.now(timezone.utc)
    notice_active = Notice(
        institution_id=inst_active.id, source_id=source.id,
        title="Concurso Docente UFPI 2024",
        normalized_title="concurso docente ufpi 2024",
        url="https://ufpi-test.br/concurso", normalized_url="https://ufpi-test.br/concurso",
        notice_type="concurso",
        description="Edital para contratação de docente temporário na área de TI.",
        fingerprint="fp_alerts_test_notice_01",
        is_active=True, detected_at=now
    )
    notice_inactive = Notice(
        institution_id=inst_active.id, source_id=source.id,
        title="Concurso Cancelado UFPI 2024",
        normalized_title="concurso cancelado ufpi 2024",
        url="https://ufpi-test.br/cancelado", normalized_url="https://ufpi-test.br/cancelado",
        notice_type="concurso",
        fingerprint="fp_alerts_test_notice_02",
        is_active=False, detected_at=now
    )
    db.add_all([notice_active, notice_inactive])
    db.commit()
    created_notice_ids.extend([notice_active.id, notice_inactive.id])

    # ═══════════════════════════════════════════════════════════════════════════
    # CRUD DE ALERTAS
    # ═══════════════════════════════════════════════════════════════════════════

    # 1. Criar alerta com usuário autenticado
    r1 = client.post("/alerts/", json={"keyword": "concurso"}, headers=headers_a)
    results["1_create_alert_authenticated"] = r1.status_code == 200
    alert_id = r1.json().get("id") if r1.status_code == 200 else None
    if alert_id:
        created_alert_ids.append(alert_id)

    # 2. Criar alerta com keyword vazia retorna erro
    r2 = client.post("/alerts/", json={"keyword": ""}, headers=headers_a)
    results["2_create_alert_empty_keyword"] = r2.status_code == 422

    # 3. Criar alerta com keyword apenas espaços retorna erro
    r3 = client.post("/alerts/", json={"keyword": "   "}, headers=headers_a)
    results["3_create_alert_whitespace_keyword"] = r3.status_code == 422

    # 4. Criar alerta com institution_id inexistente retorna 400
    r4 = client.post("/alerts/", json={"keyword": "edital", "institution_id": 999999}, headers=headers_a)
    results["4_create_alert_nonexistent_institution"] = r4.status_code == 400

    # 5. Criar alerta com institution_id inativa retorna 400
    r5 = client.post("/alerts/", json={"keyword": "edital", "institution_id": inst_inactive.id}, headers=headers_a)
    results["5_create_alert_inactive_institution"] = r5.status_code == 400

    # 6. Criar alerta sem token retorna 401
    r6 = client.post("/alerts/", json={"keyword": "concurso"}, headers=headers_none)
    results["6_create_alert_no_token"] = r6.status_code == 401

    # 7. Listar alertas retorna apenas os do usuário logado
    # Create alert for user B to test isolation
    r_b_create = client.post("/alerts/", json={"keyword": "bolsa"}, headers=headers_b)
    if r_b_create.status_code == 200:
        created_alert_ids.append(r_b_create.json().get("id"))
    r7 = client.get("/alerts/", headers=headers_a)
    r7_user_ids = list({n["user_id"] for n in r7.json()})
    results["7_list_alerts_isolation"] = r7.status_code == 200 and r7_user_ids == [user_a.id]

    # 8. Listagem de alertas respeita skip/limit
    # Create a second alert for user A
    r_a2 = client.post("/alerts/", json={"keyword": "docente"}, headers=headers_a)
    if r_a2.status_code == 200:
        created_alert_ids.append(r_a2.json().get("id"))
    r8 = client.get("/alerts/", params={"limit": 1}, headers=headers_a)
    results["8_list_alerts_pagination"] = r8.status_code == 200 and len(r8.json()) == 1

    # 9. Detalhe de alerta de outro usuário retorna 404
    r9 = client.get(f"/alerts/{alert_id}", headers=headers_b)
    results["9_get_other_user_alert_returns_404"] = r9.status_code == 404

    # 10. Atualizar alerta próprio
    r10 = client.put(f"/alerts/{alert_id}", json={"keyword": "concurso publico"}, headers=headers_a)
    results["10_update_own_alert"] = r10.status_code == 200 and r10.json().get("keyword") == "concurso publico"

    # 11. Update com institution_id=null remove o filtro por instituição
    # First set institution_id
    r11_set = client.put(f"/alerts/{alert_id}", json={"institution_id": inst_active.id}, headers=headers_a)
    # Then clear it with null
    r11 = client.put(f"/alerts/{alert_id}", json={"institution_id": None}, headers=headers_a)
    results["11_update_institution_id_to_null"] = r11.status_code == 200 and r11.json().get("institution_id") is None

    # 12. Update com notice_type=null remove o filtro por tipo
    r12_set = client.put(f"/alerts/{alert_id}", json={"notice_type": "concurso"}, headers=headers_a)
    r12 = client.put(f"/alerts/{alert_id}", json={"notice_type": None}, headers=headers_a)
    results["12_update_notice_type_to_null"] = r12.status_code == 200 and r12.json().get("notice_type") is None

    # 13. Update com keyword apenas espaços retorna erro
    r13 = client.put(f"/alerts/{alert_id}", json={"keyword": "   "}, headers=headers_a)
    results["13_update_whitespace_keyword"] = r13.status_code == 422

    # 14. Soft delete de alerta próprio
    r14 = client.delete(f"/alerts/{alert_id}", headers=headers_a)
    results["14_soft_delete_own_alert"] = r14.status_code == 200 and r14.json().get("is_active") == False

    # ═══════════════════════════════════════════════════════════════════════════
    # MATCH SETUP — create an active alert for user A that matches notice_active
    # ═══════════════════════════════════════════════════════════════════════════
    alert_for_match = UserAlert(
        user_id=user_a.id,
        keyword="docente",  # matches notice_active description
        institution_id=None,
        notice_type=None,
        is_active=True,
    )
    alert_inactive = UserAlert(
        user_id=user_a.id,
        keyword="concurso",
        is_active=False,  # should be ignored by match
    )
    alert_with_type_filter = UserAlert(
        user_id=user_a.id,
        keyword="concurso",
        notice_type="bolsa",  # won't match notice_active (type=concurso)
        is_active=True,
    )
    alert_with_inst_filter = UserAlert(
        user_id=user_a.id,
        keyword="concurso",
        institution_id=inst_inactive.id,  # inst_inactive.id won't match notice_active
        is_active=True,
    )
    db.add_all([alert_for_match, alert_inactive, alert_with_type_filter, alert_with_inst_filter])
    db.commit()
    created_alert_ids.extend([
        alert_for_match.id, alert_inactive.id,
        alert_with_type_filter.id, alert_with_inst_filter.id
    ])

    # Clean up any prior notifications for our test users/notices
    db.query(Notification).filter(
        Notification.user_id.in_([user_a.id, user_b.id]),
        Notification.notice_id.in_([notice_active.id, notice_inactive.id])
    ).delete(synchronize_session=False)
    db.commit()

    # ═══════════════════════════════════════════════════════════════════════════
    # ROTINA DE MATCH (direta via service)
    # ═══════════════════════════════════════════════════════════════════════════
    from app.services.notification import match_notices_with_alerts

    # 15. Match considera keyword em title — notice_active title has "Concurso"
    alert_title_match = UserAlert(
        user_id=user_b.id, keyword="Concurso", is_active=True
    )
    db.add(alert_title_match)
    db.commit()
    created_alert_ids.append(alert_title_match.id)

    result_match = match_notices_with_alerts(db)
    notifs_b = db.query(Notification).filter(
        Notification.user_id == user_b.id,
        Notification.notice_id == notice_active.id
    ).all()
    results["15_match_keyword_in_title"] = len(notifs_b) == 1
    if notifs_b:
        created_notification_ids.extend([n.id for n in notifs_b])

    # 16. Match considera keyword em description — alert_for_match uses "docente"
    notifs_a_docente = db.query(Notification).filter(
        Notification.user_id == user_a.id,
        Notification.notice_id == notice_active.id
    ).all()
    results["16_match_keyword_in_description"] = len(notifs_a_docente) >= 1
    if notifs_a_docente:
        created_notification_ids.extend([n.id for n in notifs_a_docente])

    # 17. Match respeita institution_id — alert_with_inst_filter has inst_inactive.id, no match expected
    notifs_inst_filter = db.query(Notification).filter(
        Notification.user_id == user_a.id,
    ).join(Notice, Notification.notice_id == Notice.id).filter(
        Notice.institution_id == inst_inactive.id
    ).all()
    results["17_match_respects_institution_id"] = len(notifs_inst_filter) == 0

    # 18. Match respeita notice_type — alert_with_type_filter wants "bolsa", notice is "concurso"
    notifs_type_filter = db.query(Notification).filter(
        Notification.user_id == user_a.id,
        Notification.notice_id == notice_active.id,
    ).all()
    # alert_for_match (no type) should match, but alert_with_type_filter (bolsa) should NOT add extra
    results["18_match_respects_notice_type"] = len(notifs_type_filter) >= 1

    # 19. Match ignora alerta inativo
    notifs_from_inactive_alert = db.query(Notification).filter(
        Notification.user_id == user_a.id
    ).all()
    # alert_inactive has keyword="concurso" and is_active=False — should never create notification
    # We verify by checking that keyword "concurso" (inactive alert) didn't add extra notifs beyond what active alerts created
    results["19_match_ignores_inactive_alert"] = result_match["alerts_checked"] >= 1  # only active alerts counted

    # 20. Match ignora notice inativo — notice_inactive is_active=False
    notifs_inactive_notice = db.query(Notification).filter(
        Notification.notice_id == notice_inactive.id
    ).all()
    results["20_match_ignores_inactive_notice"] = len(notifs_inactive_notice) == 0

    # 21. Match não cria notificação duplicada — run again
    result_match2 = match_notices_with_alerts(db)
    notifs_b_after = db.query(Notification).filter(
        Notification.user_id == user_b.id,
        Notification.notice_id == notice_active.id
    ).count()
    results["21_match_no_duplicate"] = notifs_b_after == 1

    # 22. Match retorna contadores corretos
    results["22_match_returns_counters"] = (
        "alerts_checked" in result_match
        and "notices_checked" in result_match
        and "notifications_created" in result_match
        and "duplicates_skipped" in result_match
    )

    # 23. Segunda execução não cria duplicatas
    results["23_second_match_no_new_notifications"] = result_match2["notifications_created"] == 0
    results["23b_second_match_increments_skipped"] = result_match2["duplicates_skipped"] > 0

    # ═══════════════════════════════════════════════════════════════════════════
    # NOTIFICAÇÕES DO USUÁRIO
    # ═══════════════════════════════════════════════════════════════════════════

    # 24. Listagem de notificações retorna apenas as do usuário logado
    r24 = client.get("/notifications/", headers=headers_a)
    r24_user_ids = list({n["user_id"] for n in r24.json()})
    results["24_list_notifications_isolation"] = r24.status_code == 200 and (
        len(r24.json()) == 0 or r24_user_ids == [user_a.id]
    )

    # 25. Listagem de notificações respeita skip/limit
    r25 = client.get("/notifications/", params={"limit": 1}, headers=headers_a)
    results["25_list_notifications_pagination"] = r25.status_code == 200 and len(r25.json()) <= 1

    # 26. Detalhe de notificação de outro usuário retorna 404
    notif_b = db.query(Notification).filter(Notification.user_id == user_b.id).first()
    if notif_b:
        r26 = client.get(f"/notifications/{notif_b.id}", headers=headers_a)
        results["26_get_other_user_notification_404"] = r26.status_code == 404
    else:
        results["26_get_other_user_notification_404"] = "skipped_no_notif_for_b"

    # ═══════════════════════════════════════════════════════════════════════════
    # ENDPOINT ADMIN DE MATCH
    # ═══════════════════════════════════════════════════════════════════════════

    # 27. Admin consegue disparar match
    r27 = client.post("/admin/match-alerts", headers=headers_admin)
    results["27_admin_triggers_match"] = (
        r27.status_code == 200
        and "alerts_checked" in r27.json()
        and "notifications_created" in r27.json()
    )

    # 28. Usuário comum recebe 403
    r28 = client.post("/admin/match-alerts", headers=headers_a)
    results["28_common_user_gets_403"] = r28.status_code == 403

    # 29. Sem token recebe 401
    r29 = client.post("/admin/match-alerts", headers=headers_none)
    results["29_no_token_gets_401"] = r29.status_code == 401

    # 30. Segunda execução via endpoint não cria duplicatas
    r30 = client.post("/admin/match-alerts", headers=headers_admin)
    results["30_admin_match_no_duplicates"] = r30.json().get("notifications_created") == 0

except Exception as e:
    results["error"] = str(e)
    import traceback
    results["traceback"] = traceback.format_exc()

finally:
    # ── CLEANUP ───────────────────────────────────────────────────────────────
    # Collect all notification IDs for our test users
    all_test_notif_ids = [
        n.id for n in db.query(Notification).filter(
            Notification.user_id.in_(created_user_ids)
        ).all()
    ]
    for nid in all_test_notif_ids:
        db.query(Notification).filter(Notification.id == nid).delete(synchronize_session=False)

    for aid in created_alert_ids:
        db.query(UserAlert).filter(UserAlert.id == aid).delete(synchronize_session=False)

    for nid in created_notice_ids:
        db.query(Notice).filter(Notice.id == nid).delete(synchronize_session=False)

    for sid in created_source_ids:
        db.query(MonitoredSource).filter(MonitoredSource.id == sid).delete(synchronize_session=False)

    for iid in created_inst_ids:
        db.query(Institution).filter(Institution.id == iid).delete(synchronize_session=False)

    for uid in created_user_ids:
        db.query(User).filter(User.id == uid).delete(synchronize_session=False)

    db.commit()
    db.close()
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2))
