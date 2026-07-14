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
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice

client = TestClient(app)
db = SessionLocal()
results = {}

# Test data IDs for cleanup
created_inst_ids = []
created_source_ids = []
created_notice_ids = []

try:
    # --- Setup: create test institution, source, and notices ---
    inst1 = Institution(
        name="Universidade Federal do Piauí",
        initials="UFPI",
        state="PI",
        official_site_url="https://ufpi.br",
        is_active=True,
    )
    inst2 = Institution(
        name="Instituto Federal do Maranhão",
        initials="IFMA",
        state="MA",
        official_site_url="https://ifma.edu.br",
        is_active=True,
    )
    db.add_all([inst1, inst2])
    db.commit()
    created_inst_ids.extend([inst1.id, inst2.id])

    source1 = MonitoredSource(
        institution_id=inst1.id,
        name="Portal UFPI",
        url="https://ufpi.br/editais",
        source_type="html",
        check_frequency_minutes=1440,
        is_active=True,
    )
    source2 = MonitoredSource(
        institution_id=inst2.id,
        name="Portal IFMA",
        url="https://ifma.edu.br/editais",
        source_type="html",
        check_frequency_minutes=1440,
        is_active=True,
    )
    db.add_all([source1, source2])
    db.commit()
    created_source_ids.extend([source1.id, source2.id])

    now = datetime.now(timezone.utc)
    notice1 = Notice(
        institution_id=inst1.id,
        source_id=source1.id,
        title="Edital de Concurso Público 01/2024",
        normalized_title="edital de concurso público 01/2024",
        url="https://ufpi.br/edital-01",
        normalized_url="https://ufpi.br/edital-01",
        notice_type="concurso",
        description="Concurso para docente efetivo no departamento de computação.",
        publication_date=now - timedelta(days=5),
        fingerprint="fp_test_notice_01_etapa6",
        is_active=True,
        detected_at=now - timedelta(days=3),
    )
    notice2 = Notice(
        institution_id=inst1.id,
        source_id=source1.id,
        title="Edital de Processo Seletivo 02/2024",
        normalized_title="edital de processo seletivo 02/2024",
        url="https://ufpi.br/edital-02",
        normalized_url="https://ufpi.br/edital-02",
        notice_type="processo_seletivo",
        fingerprint="fp_test_notice_02_etapa6",
        is_active=True,
        detected_at=now - timedelta(days=1),
    )
    notice3 = Notice(
        institution_id=inst2.id,
        source_id=source2.id,
        title="Edital de Bolsas IFMA 2024",
        normalized_title="edital de bolsas ifma 2024",
        url="https://ifma.edu.br/bolsas",
        normalized_url="https://ifma.edu.br/bolsas",
        notice_type="bolsa",
        fingerprint="fp_test_notice_03_etapa6",
        is_active=True,
        detected_at=now - timedelta(days=2),
    )
    notice_inactive = Notice(
        institution_id=inst1.id,
        source_id=source1.id,
        title="Edital Cancelado 99/2024",
        normalized_title="edital cancelado 99/2024",
        url="https://ufpi.br/edital-99",
        normalized_url="https://ufpi.br/edital-99",
        notice_type="edital",
        fingerprint="fp_test_notice_inactive_etapa6",
        is_active=False,
        detected_at=now - timedelta(days=10),
    )
    db.add_all([notice1, notice2, notice3, notice_inactive])
    db.commit()
    created_notice_ids.extend([notice1.id, notice2.id, notice3.id, notice_inactive.id])

    # ===== TESTS =====

    # 1. GET /notices returns public list without token (200)
    r1 = client.get("/notices/")
    results["1_list_public_no_token"] = r1.status_code == 200

    # 2. GET /notices/{id} returns detail without token (200)
    r2 = client.get(f"/notices/{notice1.id}")
    results["2_detail_public_no_token"] = r2.status_code == 200

    # 3. GET /notices/{id} non-existent returns 404
    r3 = client.get("/notices/999999")
    results["3_detail_not_found"] = r3.status_code == 404

    # 4. GET /notices/{id} inactive returns 404
    r4 = client.get(f"/notices/{notice_inactive.id}")
    results["4_detail_inactive_404"] = r4.status_code == 404

    # 5. Default listing ignores inactive notices
    r5 = client.get("/notices/")
    r5_ids = [n["id"] for n in r5.json()]
    results["5_listing_ignores_inactive"] = notice_inactive.id not in r5_ids

    # 6. limit=101 returns 422 (validation error)
    r6 = client.get("/notices/", params={"limit": 101})
    results["6_limit_over_100_rejected"] = r6.status_code == 422

    # 7. Filter by keyword (title match)
    r7 = client.get("/notices/", params={"keyword": "Concurso"})
    r7_ids = [n["id"] for n in r7.json()]
    results["7_filter_keyword_title"] = notice1.id in r7_ids and notice2.id not in r7_ids

    # 8. Filter by keyword (description match)
    r8 = client.get("/notices/", params={"keyword": "docente"})
    r8_ids = [n["id"] for n in r8.json()]
    results["8_filter_keyword_description"] = notice1.id in r8_ids

    # 9. Filter by institution_id
    r9 = client.get("/notices/", params={"institution_id": inst2.id})
    r9_ids = [n["id"] for n in r9.json()]
    results["9_filter_institution_id"] = notice3.id in r9_ids and notice1.id not in r9_ids

    # 10. Filter by state (via Institution JOIN)
    r10 = client.get("/notices/", params={"state": "MA"})
    r10_ids = [n["id"] for n in r10.json()]
    results["10_filter_state"] = notice3.id in r10_ids and notice1.id not in r10_ids

    # 11. Filter by notice_type
    r11 = client.get("/notices/", params={"notice_type": "bolsa"})
    r11_ids = [n["id"] for n in r11.json()]
    results["11_filter_notice_type"] = notice3.id in r11_ids and notice1.id not in r11_ids

    # 12. Filter by detected_after / detected_before
    after_date = (now - timedelta(days=1, hours=12)).isoformat()
    r12 = client.get("/notices/", params={"detected_after": after_date})
    r12_ids = [n["id"] for n in r12.json()]
    results["12_filter_detected_after"] = notice2.id in r12_ids and notice3.id not in r12_ids

    before_date = (now - timedelta(days=2, hours=12)).isoformat()
    r12b = client.get("/notices/", params={"detected_before": before_date})
    r12b_ids = [n["id"] for n in r12b.json()]
    results["12b_filter_detected_before"] = notice1.id in r12b_ids and notice2.id not in r12b_ids

    # 13. Ordering by detected_at desc
    r13 = client.get("/notices/")
    r13_data = r13.json()
    # notice2 (1 day ago) should come before notice3 (2 days ago) which should come before notice1 (3 days ago)
    r13_ids = [n["id"] for n in r13_data]
    # Filter only our test notices
    our_ids = [nid for nid in r13_ids if nid in created_notice_ids]
    results["13_order_detected_at_desc"] = our_ids == [notice2.id, notice3.id, notice1.id]

    # 14. Pagination with limit
    r14 = client.get("/notices/", params={"limit": 2})
    results["14_pagination_limit"] = len(r14.json()) <= 2

    # 15. Public response does NOT contain internal fields
    r15 = client.get(f"/notices/{notice1.id}")
    r15_json = r15.json()
    internal_fields = ["fingerprint", "normalized_title", "normalized_url", "content_hash"]
    results["15_no_internal_fields"] = all(f not in r15_json for f in internal_fields)

    # 16. Detail response contains institution data
    r16 = client.get(f"/notices/{notice1.id}")
    r16_json = r16.json()
    results["16_detail_has_institution"] = (
        r16_json.get("institution") is not None
        and r16_json["institution"].get("name") == "Universidade Federal do Piauí"
        and r16_json["institution"].get("state") == "PI"
    )

    # 17. skip validation (negative skip rejected)
    r17 = client.get("/notices/", params={"skip": -1})
    results["17_negative_skip_rejected"] = r17.status_code == 422

except Exception as e:
    results["error"] = str(e)

finally:
    # Cleanup all test data
    for nid in created_notice_ids:
        db.query(Notice).filter(Notice.id == nid).delete(synchronize_session=False)
    for sid in created_source_ids:
        db.query(MonitoredSource).filter(MonitoredSource.id == sid).delete(synchronize_session=False)
    for iid in created_inst_ids:
        db.query(Institution).filter(Institution.id == iid).delete(synchronize_session=False)
    db.commit()
    db.close()
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2))
