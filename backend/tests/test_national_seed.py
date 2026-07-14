"""Offline SQLite integration tests for the transactional national seed."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.catalog.loader import load_national_catalog
from app.catalog.urls import normalize_url
from app.db.base import Base
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.services import national_seed


class NationalSeedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary.name) / "national-seed.sqlite3"
        self.engine = create_engine(
            f"sqlite:///{database_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )
        self.db = self.Session()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        self.temporary.cleanup()

    def test_national_seed_has_reconciled_inventory_and_metadata(self) -> None:
        catalog = load_national_catalog()
        eligible = [
            item
            for item in catalog["institutions"]
            if item["eligibility_status"].startswith("included")
        ]
        excluded = [
            item
            for item in catalog["institutions"]
            if item["eligibility_status"].startswith("excluded")
        ]
        expected_source_total = sum(len(item["sources"]) for item in eligible)
        expected_pending = sum(
            item["coverage_status"] != "verified" for item in eligible
        )
        expected_manual_review = sum(
            item["coverage_status"] == "manual_review" for item in eligible
        )

        stats = national_seed.seed_national_catalog(self.db)
        institutions = self.db.query(Institution).all()
        sources = self.db.query(MonitoredSource).all()

        self.assertEqual(stats["institutions_created"], 318)
        self.assertEqual(stats["institutions_ignored"], len(excluded))
        self.assertEqual(stats["sources_created"], expected_source_total)
        self.assertEqual(stats["pending"], expected_pending)
        self.assertEqual(stats["manual_review"], expected_manual_review)
        self.assertEqual(stats["institutions_pending"], expected_pending)
        self.assertEqual(
            stats["institutions_manual_review"],
            expected_manual_review,
        )
        self.assertEqual(len(institutions), 318)
        self.assertEqual(len(sources), expected_source_total)
        self.assertEqual(
            sum(str(item.official_code).isdigit() for item in institutions),
            315,
        )
        self.assertEqual(
            {
                item.official_code
                for item in institutions
                if item.official_code.startswith("LAW-")
            },
            {
                "LAW-15367-IFSPB",
                "LAW-15418-UNIND",
                "LAW-15457-UFESPORTE",
            },
        )
        self.assertFalse(
            self.db.query(Institution)
            .filter(
                Institution.official_code.in_(
                    {item["official_code"] for item in excluded}
                )
            )
            .first()
        )
        self.assertTrue(all(source.is_active is False for source in sources))
        self.assertTrue(
            all(
                item.is_active is False
                for item in institutions
                if item.official_code.startswith("LAW-")
            )
        )

        by_source_id = {
            source["catalog_source_id"]: source
            for item in eligible
            for source in item["sources"]
        }
        persisted = sources[0]
        expected = by_source_id[persisted.catalog_source_id]
        self.assertEqual(persisted.url, normalize_url(expected["url"]))
        self.assertEqual(
            persisted.normalized_url,
            normalize_url(expected["url"]),
        )
        self.assertEqual(persisted.coverage_status, expected["status"])
        self.assertEqual(
            persisted.verification_http_status,
            expected["http_status"],
        )
        self.assertEqual(
            persisted.verification_final_url,
            expected["final_url"],
        )
        self.assertEqual(
            json.loads(persisted.verification_redirect_chain),
            expected["redirect_chain"],
        )
        self.assertEqual(
            json.loads(persisted.notice_categories),
            expected["categories"],
        )
        self.assertFalse(hasattr(persisted, "replaces"))

    def test_second_execution_is_idempotent_and_reports_ignored(self) -> None:
        catalog = load_national_catalog()
        eligible = [
            item
            for item in catalog["institutions"]
            if item["eligibility_status"].startswith("included")
        ]
        excluded_total = len(catalog["institutions"]) - len(eligible)
        expected_sources = sum(len(item["sources"]) for item in eligible)

        national_seed.seed_national_catalog(self.db)
        institution_count = self.db.query(Institution).count()
        source_count = self.db.query(MonitoredSource).count()

        stats = national_seed.seed_national_catalog(self.db)

        self.assertEqual(stats["created"], 0)
        self.assertEqual(stats["updated"], 0)
        self.assertEqual(stats["replaced"], 0)
        self.assertEqual(
            stats["institutions_ignored"],
            len(eligible) + excluded_total,
        )
        self.assertEqual(stats["sources_ignored"], expected_sources)
        self.assertEqual(
            self.db.query(Institution).count(),
            institution_count,
        )
        self.assertEqual(self.db.query(MonitoredSource).count(), source_count)

    def test_region_seed_is_isolated_and_includes_matching_overlay(self) -> None:
        stats = national_seed.seed_national_catalog(
            self.db,
            regions=["Centro-Oeste"],
        )
        institutions = self.db.query(Institution).all()

        self.assertEqual(stats["institutions_created"], 29)
        self.assertEqual(len(institutions), 29)
        self.assertTrue(all(item.region == "Centro-Oeste" for item in institutions))
        self.assertEqual(
            sum(item.official_code.startswith("LAW-") for item in institutions),
            2,
        )

    def test_existing_manual_fields_and_source_operations_are_preserved(self) -> None:
        catalog = load_national_catalog(regions="Centro-Oeste")
        item = next(
            institution
            for institution in catalog["institutions"]
            if institution["official_code"] == "1"
        )
        source_item = item["sources"][0]
        institution = Institution(
            official_code="1",
            name="Nome editado manualmente",
            initials="SIGLA-MANUAL",
            state="MT",
            official_site_url="https://manual.example.org/instituicao",
            logo_url="https://manual.example.org/logo.png",
            is_active=False,
        )
        self.db.add(institution)
        self.db.flush()
        source = MonitoredSource(
            institution_id=institution.id,
            catalog_source_id=source_item["catalog_source_id"],
            name="Nome operacional antigo",
            url="https://old.example.org/source",
            normalized_url="https://old.example.org/source",
            source_type="legacy",
            check_frequency_minutes=777,
            is_active=True,
        )
        self.db.add(source)
        self.db.commit()

        national_seed.seed_national_catalog(
            self.db,
            regions="Centro-Oeste",
        )
        self.db.refresh(institution)
        self.db.refresh(source)

        self.assertEqual(institution.name, "Nome editado manualmente")
        self.assertEqual(institution.initials, "SIGLA-MANUAL")
        self.assertEqual(
            institution.official_site_url,
            "https://manual.example.org/instituicao",
        )
        self.assertEqual(
            institution.logo_url,
            "https://manual.example.org/logo.png",
        )
        self.assertFalse(institution.is_active)
        self.assertEqual(source.url, normalize_url(source_item["url"]))
        self.assertEqual(
            source.normalized_url,
            normalize_url(source_item["url"]),
        )
        self.assertTrue(source.is_active)
        self.assertEqual(source.check_frequency_minutes, 777)

    def test_unique_legacy_initials_and_state_are_adopted(self) -> None:
        catalog = load_national_catalog(regions="Centro-Oeste")
        item = next(
            institution
            for institution in catalog["institutions"]
            if institution.get("official_initials")
        )
        legacy = Institution(
            name="Nome legado preservado",
            initials=item["official_initials"],
            state=item["state"],
            official_site_url=None,
            is_active=True,
        )
        self.db.add(legacy)
        self.db.commit()
        legacy_id = legacy.id

        national_seed.seed_national_catalog(
            self.db,
            regions="Centro-Oeste",
        )
        adopted = self.db.query(Institution).filter_by(id=legacy_id).one()

        self.assertEqual(adopted.official_code, item["official_code"])
        self.assertEqual(adopted.name, "Nome legado preservado")
        self.assertEqual(
            self.db.query(Institution)
            .filter(Institution.official_code == item["official_code"])
            .count(),
            1,
        )
        self.assertEqual(
            adopted.official_site_url,
            item["official_site_url"],
        )

    def test_multiple_sources_are_created_for_one_institution(self) -> None:
        catalog = load_national_catalog(regions="Nordeste")
        item = max(
            (
                institution
                for institution in catalog["institutions"]
                if institution["eligibility_status"].startswith("included")
            ),
            key=lambda institution: len(institution["sources"]),
        )
        self.assertGreaterEqual(len(item["sources"]), 2)

        national_seed.seed_national_catalog(self.db, regions="Nordeste")
        institution = (
            self.db.query(Institution)
            .filter(Institution.official_code == item["official_code"])
            .one()
        )
        source_count = (
            self.db.query(MonitoredSource)
            .filter(MonitoredSource.institution_id == institution.id)
            .count()
        )
        self.assertEqual(source_count, len(item["sources"]))

    def test_ambiguous_legacy_initials_are_not_adopted(self) -> None:
        catalog = load_national_catalog(regions="Sudeste")
        fatecs = [
            item
            for item in catalog["institutions"]
            if item.get("official_initials") == "FATEC"
            and item.get("state") == "SP"
            and item["eligibility_status"].startswith("included")
        ]
        self.assertGreater(len(fatecs), 1)

        legacy = Institution(
            name="Registro legado FATEC sem campus identificado",
            initials="FATEC",
            state="SP",
            official_site_url="https://legacy.example.org/fatec",
            is_active=True,
        )
        self.db.add(legacy)
        self.db.commit()

        with self.assertRaisesRegex(
            national_seed.NationalSeedError,
            "ambiguous across the selected catalog",
        ):
            national_seed.seed_national_catalog(self.db, regions="Sudeste")

        self.db.refresh(legacy)
        self.assertIsNone(legacy.official_code)
        self.assertEqual(self.db.query(Institution).count(), 1)

    def test_source_catalog_id_conflict_requires_explicit_replaces(self) -> None:
        catalog = load_national_catalog(regions="Centro-Oeste")
        item = next(
            institution
            for institution in catalog["institutions"]
            if any(not source.get("replaces") for source in institution["sources"])
        )
        source_item = next(
            source for source in item["sources"] if not source.get("replaces")
        )
        institution = Institution(
            name=item["official_name"],
            initials=item["initials"],
            state=item["state"],
            official_code=item["official_code"],
            official_site_url=item.get("official_site_url"),
            is_active=True,
        )
        self.db.add(institution)
        self.db.flush()
        conflicting = MonitoredSource(
            institution_id=institution.id,
            catalog_source_id="manual-conflicting-source-id",
            name="Fonte manual com ID próprio",
            url=normalize_url(source_item["url"]),
            normalized_url=normalize_url(source_item["url"]),
            source_type="manual",
            check_frequency_minutes=321,
            is_active=True,
        )
        self.db.add(conflicting)
        self.db.commit()

        with self.assertRaisesRegex(
            national_seed.NationalSeedError,
            "add an explicit replaces rule",
        ):
            national_seed.seed_national_catalog(
                self.db,
                regions="Centro-Oeste",
            )

        self.db.refresh(conflicting)
        self.assertEqual(
            conflicting.catalog_source_id,
            "manual-conflicting-source-id",
        )
        self.assertTrue(conflicting.is_active)
        self.assertEqual(self.db.query(MonitoredSource).count(), 1)

    def test_source_replaces_legacy_row_without_losing_activation(self) -> None:
        catalog = load_national_catalog(regions="Nordeste")
        selected: tuple[dict[str, object], dict[str, object], str] | None = None
        for item in catalog["institutions"]:
            for source in item["sources"]:
                replacement_url = next(
                    (
                        value
                        for value in source.get("replaces", [])
                        if str(value).startswith(("http://", "https://"))
                    ),
                    None,
                )
                if replacement_url:
                    selected = (item, source, replacement_url)
                    break
            if selected:
                break
        self.assertIsNotNone(
            selected,
            "Northeast corrections must preserve legacy URLs",
        )
        item, source_item, replacement_url = selected  # type: ignore[misc]
        institution = Institution(
            name=item["official_name"],
            initials=item["initials"],
            state=item["state"],
            official_code=item["official_code"],
            is_active=True,
        )
        self.db.add(institution)
        self.db.flush()
        legacy_source = MonitoredSource(
            institution_id=institution.id,
            name="Fonte legada",
            url=replacement_url,
            normalized_url=normalize_url(replacement_url),
            source_type="legacy",
            check_frequency_minutes=333,
            is_active=True,
        )
        self.db.add(legacy_source)
        self.db.commit()
        legacy_id = legacy_source.id

        stats = national_seed.seed_national_catalog(
            self.db,
            regions="Nordeste",
        )
        replaced = (
            self.db.query(MonitoredSource)
            .filter_by(id=legacy_id)
            .one()
        )

        self.assertGreaterEqual(stats["replaced"], 1)
        self.assertEqual(
            replaced.catalog_source_id,
            source_item["catalog_source_id"],
        )
        self.assertEqual(
            replaced.normalized_url,
            normalize_url(source_item["url"]),
        )
        self.assertTrue(replaced.is_active)
        self.assertEqual(replaced.check_frequency_minutes, 333)

    def test_same_name_without_explicit_rule_is_not_adopted(self) -> None:
        catalog = load_national_catalog(regions="Centro-Oeste")
        item = next(
            institution
            for institution in catalog["institutions"]
            if any(not source.get("replaces") for source in institution["sources"])
        )
        source_item = next(
            source for source in item["sources"] if not source.get("replaces")
        )
        institution = Institution(
            name=item["official_name"],
            initials=item["initials"],
            state=item["state"],
            official_code=item["official_code"],
            is_active=True,
        )
        self.db.add(institution)
        self.db.flush()
        manual_source = MonitoredSource(
            institution_id=institution.id,
            name=source_item["name"],
            url="https://manual.example.org/unrelated",
            normalized_url="https://manual.example.org/unrelated",
            source_type="manual",
            check_frequency_minutes=321,
            is_active=True,
        )
        self.db.add(manual_source)
        self.db.commit()
        manual_id = manual_source.id

        national_seed.seed_national_catalog(
            self.db,
            regions="Centro-Oeste",
        )
        self.db.refresh(manual_source)

        self.assertEqual(manual_source.id, manual_id)
        self.assertIsNone(manual_source.catalog_source_id)
        self.assertEqual(
            manual_source.normalized_url,
            "https://manual.example.org/unrelated",
        )
        self.assertTrue(manual_source.is_active)
        self.assertEqual(manual_source.check_frequency_minutes, 321)
        self.assertEqual(
            self.db.query(MonitoredSource)
            .filter(MonitoredSource.institution_id == institution.id)
            .count(),
            len(item["sources"]) + 1,
        )

    def test_error_rolls_back_all_writes(self) -> None:
        valid = load_national_catalog(
            regions="Centro-Oeste",
        )["institutions"][0]
        broken_catalog = {
            "metadata": {},
            "institutions": [
                valid,
                {"eligibility_status": "included"},
            ],
        }
        with patch.object(
            national_seed,
            "load_national_catalog",
            return_value=broken_catalog,
        ):
            with self.assertRaises(KeyError):
                national_seed.seed_national_catalog(
                    self.db,
                    regions="Centro-Oeste",
                )
        self.assertEqual(self.db.query(Institution).count(), 0)
        self.assertEqual(self.db.query(MonitoredSource).count(), 0)


if __name__ == "__main__":
    unittest.main()
