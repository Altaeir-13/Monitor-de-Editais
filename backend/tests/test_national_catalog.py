"""Offline contract tests for the canonical INEP 2024 institution catalog.

The committed JSON is always tested.  To additionally verify the raw official
CSV, set ``INEP_2024_IES_CSV`` or run this file with ``--csv PATH``.  No test in
this module accesses the network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import unittest
from collections import Counter
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = BACKEND_DIR / "app" / "catalog" / "institutions_2024.json"
EXPECTED_SHA256 = "aaa37fb9433d005686616bb9e48c5d7083526fdcc171973e787eed35a2ee349d"
EXPECTED_MD5 = "dbe25e67857aa68b12beaeffa194f53f"

REGION_BY_STATE = {
    "AC": "Norte",
    "AL": "Nordeste",
    "AM": "Norte",
    "AP": "Norte",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "GO": "Centro-Oeste",
    "MA": "Nordeste",
    "MG": "Sudeste",
    "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "PA": "Norte",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "PR": "Sul",
    "RJ": "Sudeste",
    "RN": "Nordeste",
    "RO": "Norte",
    "RR": "Norte",
    "RS": "Sul",
    "SC": "Sul",
    "SE": "Nordeste",
    "SP": "Sudeste",
    "TO": "Norte",
}

EXPECTED_REGION_COUNTS = {
    "Norte": 24,
    "Nordeste": 66,
    "Centro-Oeste": 27,
    "Sudeste": 166,
    "Sul": 34,
}

EXPECTED_STATE_COUNTS = {
    "AC": 2,
    "AL": 4,
    "AM": 3,
    "AP": 3,
    "BA": 10,
    "CE": 7,
    "DF": 5,
    "ES": 5,
    "GO": 14,
    "MA": 4,
    "MG": 22,
    "MS": 4,
    "MT": 4,
    "PA": 6,
    "PB": 4,
    "PE": 26,
    "PI": 4,
    "PR": 14,
    "RJ": 29,
    "RN": 5,
    "RO": 2,
    "RR": 3,
    "RS": 11,
    "SC": 9,
    "SE": 2,
    "SP": 110,
    "TO": 5,
}

EXPECTED_CATEGORY_COUNTS = {1: 122, 2: 139, 3: 28, 7: 28}
EXPECTED_ORGANIZATION_COUNTS = {1: 116, 2: 8, 3: 152, 4: 39, 5: 2}
EXPECTED_FALLBACK_CODES = {
    "5633",
    "15680",
    "21713",
    "23438",
    "23459",
    "23700",
    "23705",
    "24672",
}

EXPECTED_FIELDS = {
    "official_code",
    "official_name",
    "official_initials",
    "initials",
    "initials_origin",
    "region",
    "state",
    "headquarters_city",
    "municipality_code",
    "administrative_category_code",
    "administrative_category_label",
    "academic_organization_code",
    "academic_organization_label",
    "census_situation",
    "current_situation",
    "eligibility_status",
    "eligibility_reason",
    "official_site_url",
    "inventory_source_url",
    "inventory_reference_date",
}

CSV_OVERRIDE: Path | None = None


class NationalCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.metadata = cls.catalog["metadata"]
        cls.institutions = cls.catalog["institutions"]

    def test_schema_and_pinned_provenance(self) -> None:
        self.assertEqual(self.catalog["schema_version"], 1)
        self.assertEqual(
            self.metadata["url"],
            "https://download.inep.gov.br/microdados/"
            "microdados_censo_da_educacao_superior_2024.zip",
        )
        self.assertEqual(
            self.metadata["member"],
            "microdados_censo_da_educacao_superior_2024/dados/"
            "MICRODADOS_ED_SUP_IES_2024.CSV",
        )
        self.assertEqual(
            self.metadata["official_md5_manifest_name"],
            "MICRODADOS_CADASTRO_IES_2024.csv",
        )
        self.assertEqual(
            self.metadata["hashes"],
            {"sha256": EXPECTED_SHA256, "md5": EXPECTED_MD5},
        )
        self.assertEqual(self.metadata["reference_date"], "2024-12-31")
        self.assertEqual(
            self.metadata["filter"], {"NU_ANO_CENSO": 2024, "TP_REDE": 1}
        )
        self.assertEqual(self.metadata["raw_total"], 317)

    def test_total_fields_and_numeric_unique_codes(self) -> None:
        self.assertEqual(len(self.institutions), 317)
        codes = [institution["official_code"] for institution in self.institutions]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(isinstance(code, str) and code.isdigit() for code in codes))
        self.assertEqual(codes, sorted(codes, key=int))
        for institution in self.institutions:
            self.assertEqual(set(institution), EXPECTED_FIELDS)

    def test_region_and_state_counts(self) -> None:
        self.assertEqual(
            Counter(item["region"] for item in self.institutions),
            Counter(EXPECTED_REGION_COUNTS),
        )
        self.assertEqual(
            Counter(item["state"] for item in self.institutions),
            Counter(EXPECTED_STATE_COUNTS),
        )
        for institution in self.institutions:
            self.assertEqual(
                institution["region"], REGION_BY_STATE[institution["state"]]
            )

    def test_category_and_organization_counts_and_labels(self) -> None:
        self.assertEqual(
            Counter(
                item["administrative_category_code"] for item in self.institutions
            ),
            Counter(EXPECTED_CATEGORY_COUNTS),
        )
        self.assertEqual(
            Counter(item["academic_organization_code"] for item in self.institutions),
            Counter(EXPECTED_ORGANIZATION_COUNTS),
        )
        category_labels = {
            1: "Pública Federal",
            2: "Pública Estadual",
            3: "Pública Municipal",
            7: "Especial",
        }
        organization_labels = {
            1: "Universidade",
            2: "Centro Universitário",
            3: "Faculdade",
            4: "Instituto Federal",
            5: "Centro Federal de Educação Tecnológica",
        }
        for institution in self.institutions:
            self.assertEqual(
                institution["administrative_category_label"],
                category_labels[institution["administrative_category_code"]],
            )
            self.assertEqual(
                institution["academic_organization_label"],
                organization_labels[institution["academic_organization_code"]],
            )

    def test_initials_fallback_is_explicit_and_limited_to_eight_records(self) -> None:
        fallback = {
            item["official_code"]: item
            for item in self.institutions
            if item["initials_origin"] == "generated_fallback"
        }
        self.assertEqual(set(fallback), EXPECTED_FALLBACK_CODES)
        for code, institution in fallback.items():
            self.assertIsNone(institution["official_initials"])
            self.assertEqual(institution["initials"], f"IES-{code}")
        for institution in self.institutions:
            if institution["official_code"] not in fallback:
                self.assertEqual(institution["initials_origin"], "official")
                self.assertEqual(
                    institution["initials"], institution["official_initials"]
                )

    def test_inventory_review_defaults(self) -> None:
        for institution in self.institutions:
            self.assertTrue(institution["official_name"])
            self.assertTrue(institution["headquarters_city"])
            self.assertTrue(institution["municipality_code"].isdigit())
            self.assertEqual(
                institution["census_situation"], "included_in_census_2024"
            )
            self.assertEqual(institution["current_situation"], "manual_review")
            self.assertEqual(institution["eligibility_status"], "included")
            self.assertIsNone(institution["eligibility_reason"])
            self.assertIsNone(institution["official_site_url"])
            self.assertEqual(
                institution["inventory_source_url"], self.metadata["url"]
            )
            self.assertEqual(institution["inventory_reference_date"], "2024-12-31")

    def test_raw_csv_hash_when_provided(self) -> None:
        csv_setting = CSV_OVERRIDE or (
            Path(os.environ["INEP_2024_IES_CSV"])
            if os.environ.get("INEP_2024_IES_CSV")
            else None
        )
        if csv_setting is None:
            self.skipTest("set INEP_2024_IES_CSV or pass --csv to verify raw hashes")
        self.assertTrue(csv_setting.is_file(), f"raw CSV not found: {csv_setting}")
        data = csv_setting.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(
            hashlib.md5(data).hexdigest(),  # noqa: S324 - provenance checksum
            EXPECTED_MD5,
        )


def _parse_test_args(argv: list[str]) -> tuple[Path | None, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--csv", type=Path)
    args, unittest_args = parser.parse_known_args(argv[1:])
    return args.csv, [argv[0], *unittest_args]


if __name__ == "__main__":
    CSV_OVERRIDE, remaining_argv = _parse_test_args(sys.argv)
    unittest.main(argv=remaining_argv)
