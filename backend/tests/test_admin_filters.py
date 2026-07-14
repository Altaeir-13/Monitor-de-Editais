"""Regression tests for national filters in the legacy admin CRUD services."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

DATABASE_PATH = (
    Path(tempfile.gettempdir())
    / f"monitor_editais_admin_filters_{uuid4().hex}.sqlite3"
)
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{DATABASE_PATH.as_posix()}",
        "SECRET_KEY": "admin-filter-test-secret-key-123456789",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CRAWLER_SCHEDULER_ENABLED": "false",
    }
)

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.schemas.monitored_source import MonitoredSourceCreate
from app.services.institution import get_institutions
from app.services.monitored_source import create_source, get_sources


class AdminFilterRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls) -> None:
        engine.dispose()
        DATABASE_PATH.unlink(missing_ok=True)

    def setUp(self) -> None:
        self.db = SessionLocal()
        self.db.query(MonitoredSource).delete()
        self.db.query(Institution).delete()
        self.db.commit()

        self.north = Institution(
            name="Instituição Norte",
            initials="IN",
            state="AM",
            official_site_url="https://north.example.edu.br",
            official_code="TEST-N",
            region="Norte",
            administrative_category_code=1,
            academic_organization_code=1,
            eligibility_status="included",
            source_discovery_status="partial",
            is_active=True,
        )
        self.south = Institution(
            name="Instituição Sul",
            initials="IS",
            state="RS",
            official_site_url="https://south.example.edu.br",
            official_code="TEST-S",
            region="Sul",
            administrative_category_code=2,
            academic_organization_code=3,
            eligibility_status="included",
            source_discovery_status="manual_review",
            is_active=False,
        )
        self.pending = Institution(
            name="Instituição Sem Fonte",
            initials="ISF",
            state="DF",
            official_site_url=None,
            official_code="TEST-P",
            region="Centro-Oeste",
            administrative_category_code=1,
            academic_organization_code=4,
            eligibility_status="included_pending_activation",
            source_discovery_status="source_not_found",
            is_active=True,
        )
        self.db.add_all([self.north, self.south, self.pending])
        self.db.flush()
        self.north_source = MonitoredSource(
            institution_id=self.north.id,
            name="Fonte Norte",
            url="https://north.example.edu.br/editais",
            normalized_url="https://north.example.edu.br/editais",
            source_type="HTML_STATIC",
            coverage_status="partial",
            check_frequency_minutes=1440,
            is_active=False,
        )
        self.south_source = MonitoredSource(
            institution_id=self.south.id,
            name="Fonte Sul",
            url="https://south.example.edu.br/editais",
            normalized_url="https://south.example.edu.br/editais",
            source_type="HTML_STATIC",
            coverage_status="manual_review",
            check_frequency_minutes=1440,
            is_active=True,
        )
        self.db.add_all([self.north_source, self.south_source])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_institution_filters_preserve_legacy_listing(self) -> None:
        self.assertEqual(len(get_institutions(self.db)), 3)
        self.assertEqual(get_institutions(self.db, region="Norte"), [self.north])
        self.assertEqual(get_institutions(self.db, state="rs"), [self.south])
        self.assertEqual(
            get_institutions(self.db, administrative_category_code=2),
            [self.south],
        )
        self.assertEqual(
            get_institutions(self.db, academic_organization_code=4),
            [self.pending],
        )
        self.assertEqual(
            get_institutions(
                self.db,
                eligibility_status="included_pending_activation",
            ),
            [self.pending],
        )
        self.assertEqual(
            get_institutions(self.db, coverage_status="manual_review"),
            [self.south],
        )
        self.assertEqual(
            get_institutions(self.db, is_active=False),
            [self.south],
        )
        self.assertEqual(
            get_institutions(self.db, has_source=False),
            [self.pending],
        )
        self.assertEqual(
            get_institutions(self.db, manual_review=True),
            [self.south],
        )

        self.pending.eligibility_status = None
        self.pending.source_discovery_status = None
        self.db.commit()
        self.assertEqual(
            get_institutions(self.db, manual_review=False),
            [self.north, self.pending],
        )

    def test_source_filters_and_inactive_default(self) -> None:
        self.assertEqual(len(get_sources(self.db)), 2)
        self.assertEqual(get_sources(self.db, region="Norte"), [self.north_source])
        self.assertEqual(get_sources(self.db, state="rs"), [self.south_source])
        self.assertEqual(
            get_sources(self.db, administrative_category_code=2),
            [self.south_source],
        )
        self.assertEqual(
            get_sources(self.db, academic_organization_code=1),
            [self.north_source],
        )
        self.assertEqual(
            get_sources(self.db, coverage_status="manual_review"),
            [self.south_source],
        )
        self.assertEqual(
            get_sources(self.db, verification_status="partial"),
            [self.north_source],
        )
        self.assertEqual(
            get_sources(self.db, institution_active=False),
            [self.south_source],
        )
        self.assertEqual(
            get_sources(self.db, source_active=True),
            [self.south_source],
        )
        self.assertEqual(
            get_sources(self.db, manual_review=True),
            [self.south_source],
        )

        self.north.eligibility_status = None
        self.north.source_discovery_status = None
        self.north_source.coverage_status = None
        self.db.commit()
        self.assertEqual(
            get_sources(self.db, manual_review=False),
            [self.north_source],
        )

        created = create_source(
            self.db,
            MonitoredSourceCreate(
                institution_id=self.pending.id,
                name="Nova fonte",
                url="HTTPS://PENDING.EXAMPLE.EDU.BR:443/editais/",
                source_type="HTML_STATIC",
            ),
        )
        self.assertEqual(
            created.url,
            "https://pending.example.edu.br/editais",
        )
        self.assertEqual(created.normalized_url, created.url)
        self.assertFalse(created.is_active)


if __name__ == "__main__":
    unittest.main()
