"""Offline reconciliation tests for national catalog eligibility totals."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.catalog.loader import load_national_catalog


class CatalogEligibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_national_catalog()
        cls.metadata = cls.catalog["metadata"]
        cls.institutions = cls.catalog["institutions"]
        cls.by_code = {
            item["official_code"]: item for item in cls.institutions
        }

    def test_reconciled_inventory_and_source_totals(self) -> None:
        eligible = [
            item
            for item in self.institutions
            if item["eligibility_status"].startswith("included")
        ]
        excluded = [
            item
            for item in self.institutions
            if item["eligibility_status"].startswith("excluded")
        ]
        all_sources = [
            source
            for institution in self.institutions
            for source in institution["sources"]
        ]
        eligible_sources = [
            source for institution in eligible for source in institution["sources"]
        ]
        excluded_sources = [
            source for institution in excluded for source in institution["sources"]
        ]

        self.assertEqual(self.metadata["raw_total"], 317)
        self.assertEqual(self.metadata["eligible_census_total"], 315)
        self.assertEqual(self.metadata["post_census_total"], 3)
        self.assertEqual(self.metadata["coverage_target_total"], 318)
        self.assertEqual(len(self.institutions), 320)
        self.assertEqual(len(eligible), 318)
        self.assertEqual(len(excluded), 2)
        self.assertEqual(len(all_sources), 303)
        self.assertEqual(len(eligible_sources), 302)
        self.assertEqual(len(excluded_sources), 1)

    def test_unc_remains_excluded_pending_scope_review(self) -> None:
        unc = self.by_code["441"]
        self.assertEqual(
            unc["eligibility_status"], "excluded_scope_manual_review"
        )
        self.assertEqual(unc["coverage_status"], "manual_review")
        self.assertEqual(
            unc["eligibility_reason"],
            "A classificação especial no Censo 2024 e a natureza jurídica "
            "comunitária exigem revisão manual de escopo; a instituição "
            "permanece no inventário bruto sem inclusão automática no alvo "
            "operacional.",
        )
        self.assertEqual(unc["sources"], [])

    def test_uniuv_remains_excluded_with_historical_source(self) -> None:
        uniuv = self.by_code["649"]
        self.assertEqual(uniuv["eligibility_status"], "excluded_inactive")
        self.assertEqual(uniuv["coverage_status"], "inactive")
        self.assertEqual(len(uniuv["sources"]), 1)
        self.assertEqual(
            uniuv["sources"][0]["catalog_source_id"],
            "inep-649-uniuv-editais-arquivo",
        )
        self.assertEqual(uniuv["sources"][0]["status"], "inactive")
        self.assertFalse(uniuv["sources"][0]["is_active"])


if __name__ == "__main__":
    unittest.main()
