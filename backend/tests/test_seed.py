import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4


backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

test_db_path = (
    Path(tempfile.gettempdir())
    / f"monitor_editais_seed_{uuid4().hex}.db"
)
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{test_db_path.as_posix()}",
        "SECRET_KEY": "test-secret-key-for-seed-tests-123456789",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CRAWLER_SCHEDULER_ENABLED": "false",
    }
)

from app.catalog.loader import load_national_catalog
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.services.northeast_seed import seed_northeast_institutions


Base.metadata.create_all(bind=engine)
db = SessionLocal()
results: dict[str, bool] = {}

try:
    expected_catalog = load_national_catalog(regions="Nordeste")
    expected_institutions = [
        item
        for item in expected_catalog["institutions"]
        if item["eligibility_status"].startswith("included")
    ]
    expected_sources = sum(
        len(item["sources"]) for item in expected_institutions
    )

    first_summary = seed_northeast_institutions(db=db)
    first_institutions = db.query(Institution).count()
    first_sources = db.query(MonitoredSource).count()
    first_all_inactive = all(
        source.is_active is False
        for source in db.query(MonitoredSource).all()
    )

    second_summary = seed_northeast_institutions(db=db)
    second_institutions = db.query(Institution).count()
    second_sources = db.query(MonitoredSource).count()

    results["1_first_seed_returns_summary"] = isinstance(first_summary, dict)
    results["2_wrapper_uses_national_region"] = (
        first_institutions == len(expected_institutions)
        and first_sources == expected_sources
    )
    results["3_new_sources_are_inactive"] = first_all_inactive
    results["4_second_seed_returns_summary"] = isinstance(second_summary, dict)
    results["5_institution_count_is_idempotent"] = (
        second_institutions == first_institutions
    )
    results["6_source_count_is_idempotent"] = second_sources == first_sources
    results["7_second_seed_has_no_writes"] = (
        second_summary["created"] == 0
        and second_summary["updated"] == 0
    )
    results["8_second_seed_reports_ignored_sources"] = (
        second_summary["sources_ignored"] == expected_sources
    )
finally:
    db.close()
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
