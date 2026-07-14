"""Disposable SQLite upgrade/downgrade checks for the national migration."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


class NationalMigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database_path = (
            Path(self.temporary.name) / "national-migration.sqlite3"
        )
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        os.environ.update(
            {
                "ENVIRONMENT": "test",
                "DATABASE_URL": self.database_url,
                "SECRET_KEY": "national-migration-test-secret",
                "ALGORITHM": "HS256",
                "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
                "CRAWLER_SCHEDULER_ENABLED": "false",
            }
        )
        self.alembic_config = Config(str(backend_path / "alembic.ini"))

        # Alembic imports the singleton settings object once per test process.
        # Point that singleton at this method's disposable database as well.
        from app.core.config import settings

        settings.DATABASE_URL = self.database_url

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _inspector(self):
        engine = create_engine(self.database_url)
        return engine, inspect(engine)

    def test_upgrade_backfills_legacy_rows(self) -> None:
        command.upgrade(self.alembic_config, "2e66bacc41d6")
        engine = create_engine(self.database_url)
        with engine.begin() as connection:
            result = connection.execute(
                text(
                    "INSERT INTO institutions "
                    "(name, initials, state, official_site_url, is_active) "
                    "VALUES (:name, :initials, :state, :url, :active)"
                ),
                {
                    "name": "Instituição legada",
                    "initials": "LEG",
                    "state": "DF",
                    "url": "https://legacy.example.org",
                    "active": True,
                },
            )
            institution_id = result.lastrowid
            connection.execute(
                text(
                    "INSERT INTO monitored_sources "
                    "(institution_id, name, url, source_type, "
                    "check_frequency_minutes, is_active) "
                    "VALUES (:institution_id, :name, :url, :source_type, "
                    ":frequency, :active)"
                ),
                {
                    "institution_id": institution_id,
                    "name": "Fonte legada",
                    "url": "https://legacy.example.org/editais",
                    "source_type": "HTML_STATIC",
                    "frequency": 1440,
                    "active": True,
                },
            )
        engine.dispose()

        command.upgrade(self.alembic_config, "head")
        engine = create_engine(self.database_url)
        with engine.connect() as connection:
            institution = connection.execute(
                text(
                    "SELECT eligibility_status, source_discovery_status "
                    "FROM institutions"
                )
            ).mappings().one()
            source = connection.execute(
                text(
                    "SELECT url, normalized_url, coverage_status "
                    "FROM monitored_sources"
                )
            ).mappings().one()
        engine.dispose()

        self.assertEqual(institution["eligibility_status"], "included_legacy")
        self.assertEqual(institution["source_discovery_status"], "manual_review")
        self.assertEqual(source["normalized_url"], source["url"])
        self.assertEqual(source["coverage_status"], "manual_review")

    def test_downgrade_after_seed_preserves_legacy_not_null_contract(self) -> None:
        command.upgrade(self.alembic_config, "head")

        from app.models.institution import Institution
        from app.models.monitored_source import MonitoredSource
        from app.services.national_seed import seed_national_catalog

        engine = create_engine(self.database_url)
        Session = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )
        db = Session()
        try:
            first = seed_national_catalog(db)
            self.assertEqual(first["institutions_created"], 318)
            self.assertEqual(first["sources_created"], 302)
        finally:
            db.close()
            engine.dispose()

        command.downgrade(self.alembic_config, "2e66bacc41d6")
        engine, inspector = self._inspector()
        with engine.connect() as connection:
            institution_total = connection.scalar(
                text("SELECT COUNT(*) FROM institutions")
            )
            source_total = connection.scalar(
                text("SELECT COUNT(*) FROM monitored_sources")
            )
            null_sites = connection.scalar(
                text(
                    "SELECT COUNT(*) FROM institutions "
                    "WHERE official_site_url IS NULL"
                )
            )
        self.assertEqual(institution_total, 318)
        self.assertEqual(source_total, 302)
        self.assertEqual(null_sites, 0)
        self.assertFalse(
            {
                column["name"]
                for column in inspector.get_columns("institutions")
            }
            & {"official_code", "inventory_source_url"}
        )
        engine.dispose()

        command.upgrade(self.alembic_config, "head")
        engine = create_engine(self.database_url)
        Session = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )
        db = Session()
        try:
            recovered = seed_national_catalog(db)
            repeated = seed_national_catalog(db)
            self.assertEqual(recovered["institutions_created"], 0)
            self.assertEqual(recovered["sources_created"], 0)
            self.assertEqual(db.query(Institution).count(), 318)
            self.assertEqual(db.query(MonitoredSource).count(), 302)
            post_census = (
                db.query(Institution)
                .filter(Institution.official_code.like("LAW-%"))
                .all()
            )
            self.assertEqual(len(post_census), 3)
            self.assertTrue(
                all(item.official_site_url is None for item in post_census)
            )
            self.assertEqual(repeated["created"], 0)
            self.assertEqual(repeated["updated"], 0)
        finally:
            db.close()
            engine.dispose()

    def test_upgrade_downgrade_upgrade_seed_and_constraints(self) -> None:
        command.upgrade(self.alembic_config, "head")

        engine, inspector = self._inspector()
        institution_columns = {
            item["name"]: item
            for item in inspector.get_columns("institutions")
        }
        source_columns = {
            item["name"]: item
            for item in inspector.get_columns("monitored_sources")
        }
        institution_uniques = {
            item["name"]: tuple(item["column_names"])
            for item in inspector.get_unique_constraints("institutions")
        }
        source_uniques = {
            item["name"]: tuple(item["column_names"])
            for item in inspector.get_unique_constraints("monitored_sources")
        }

        self.assertTrue(institution_columns["official_site_url"]["nullable"])
        self.assertIn("eligibility_status", institution_columns)
        self.assertIn("inventory_reference_date", institution_columns)
        self.assertIn("normalized_url", source_columns)
        self.assertIn("verification_http_status", source_columns)
        self.assertIn("capture_validated_at", source_columns)
        self.assertEqual(
            institution_uniques["uq_institutions_official_code"],
            ("official_code",),
        )
        self.assertEqual(
            source_uniques["uq_monitored_sources_catalog_source_id"],
            ("catalog_source_id",),
        )
        self.assertEqual(
            source_uniques[
                "uq_monitored_sources_institution_normalized_url"
            ],
            ("institution_id", "normalized_url"),
        )
        engine.dispose()

        command.downgrade(self.alembic_config, "2e66bacc41d6")
        engine, inspector = self._inspector()
        downgraded_institution_columns = {
            item["name"]: item
            for item in inspector.get_columns("institutions")
        }
        downgraded_source_columns = {
            item["name"]: item
            for item in inspector.get_columns("monitored_sources")
        }
        self.assertFalse(
            downgraded_institution_columns["official_site_url"]["nullable"]
        )
        self.assertNotIn("official_code", downgraded_institution_columns)
        self.assertNotIn("catalog_source_id", downgraded_source_columns)
        engine.dispose()

        command.upgrade(self.alembic_config, "head")

        from app.models.institution import Institution
        from app.models.monitored_source import MonitoredSource
        from app.services.national_seed import seed_national_catalog

        engine = create_engine(self.database_url)
        Session = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
        )
        db = Session()
        try:
            first = seed_national_catalog(db)
            second = seed_national_catalog(db)
            self.assertEqual(first["institutions_created"], 318)
            self.assertEqual(first["sources_created"], 302)
            self.assertEqual(second["created"], 0)
            self.assertEqual(second["updated"], 0)
            self.assertEqual(db.query(Institution).count(), 318)
            self.assertEqual(db.query(MonitoredSource).count(), 302)

            source = db.query(MonitoredSource).first()
            self.assertIsNotNone(source.normalized_url)
            source.capture_validated_at = datetime.now(timezone.utc)
            source.capture_evidence = "sqlite disposable validation"
            db.commit()
            db.refresh(source)
            self.assertIsNotNone(source.capture_validated_at)
            self.assertEqual(
                source.capture_evidence,
                "sqlite disposable validation",
            )

            suffix = uuid4().hex
            first_institution = Institution(
                official_code=f"TEST-A-{suffix}",
                name="Teste A",
                initials="TA",
                state="DF",
                official_site_url=None,
                is_active=True,
            )
            second_institution = Institution(
                official_code=f"TEST-B-{suffix}",
                name="Teste B",
                initials="TB",
                state="DF",
                official_site_url=None,
                is_active=True,
            )
            db.add_all([first_institution, second_institution])
            db.flush()

            shared_url = f"https://example.invalid/shared-{suffix}"
            first_source = MonitoredSource(
                institution_id=first_institution.id,
                catalog_source_id=f"test-source-a-{suffix}",
                name="Fonte A",
                url=shared_url,
                normalized_url=shared_url,
                source_type="test",
                check_frequency_minutes=1440,
            )
            second_source = MonitoredSource(
                institution_id=second_institution.id,
                catalog_source_id=f"test-source-b-{suffix}",
                name="Fonte B",
                url=shared_url,
                normalized_url=shared_url,
                source_type="test",
                check_frequency_minutes=1440,
            )
            db.add_all([first_source, second_source])
            db.commit()
            self.assertFalse(first_source.is_active)
            self.assertFalse(second_source.is_active)

            duplicate_url = MonitoredSource(
                institution_id=first_institution.id,
                catalog_source_id=f"test-source-c-{suffix}",
                name="Fonte duplicada na instituição",
                url=shared_url,
                normalized_url=shared_url,
                source_type="test",
                check_frequency_minutes=1440,
            )
            db.add(duplicate_url)
            with self.assertRaises(IntegrityError):
                db.commit()
            db.rollback()

            duplicate_catalog_id = MonitoredSource(
                institution_id=second_institution.id,
                catalog_source_id=f"test-source-a-{suffix}",
                name="Fonte com ID duplicado",
                url=f"https://example.invalid/other-{suffix}",
                normalized_url=f"https://example.invalid/other-{suffix}",
                source_type="test",
                check_frequency_minutes=1440,
            )
            db.add(duplicate_catalog_id)
            with self.assertRaises(IntegrityError):
                db.commit()
            db.rollback()
        finally:
            db.close()
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
