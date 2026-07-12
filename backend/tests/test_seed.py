import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

test_db_path = Path(tempfile.gettempdir()) / f"monitor_editais_seed_{uuid4().hex}.db"
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

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.services.northeast_seed import seed_northeast_institutions


Base.metadata.create_all(bind=engine)
db = SessionLocal()
results: dict[str, bool] = {}

try:
    first_summary = seed_northeast_institutions(db=db)
    first_institutions = db.query(Institution).count()
    first_sources = db.query(MonitoredSource).count()
    second_summary = seed_northeast_institutions(db=db)
    second_institutions = db.query(Institution).count()
    second_sources = db.query(MonitoredSource).count()
    results["1_first_seed_returns_summary"] = isinstance(first_summary, dict)
    results["2_catalog_is_not_empty"] = first_institutions > 0 and first_sources > 0
    results["3_second_seed_returns_summary"] = isinstance(second_summary, dict)
    results["4_institution_count_is_idempotent"] = second_institutions == first_institutions
    results["5_source_count_is_idempotent"] = second_sources == first_sources
finally:
    db.close()
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
