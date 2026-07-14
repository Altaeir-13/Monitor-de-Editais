"""Offline validation tests for regional source manifests and URL identity."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.catalog.loader as loader
from app.catalog.urls import URLNormalizationError, normalize_url


class SourceManifestTest(unittest.TestCase):
    def test_national_contract_and_post_census_overlays(self) -> None:
        catalog = loader.load_national_catalog()
        metadata = catalog["metadata"]
        institutions = catalog["institutions"]
        self.assertEqual(metadata["raw_total"], 317)
        self.assertEqual(metadata["eligible_census_total"], 315)
        self.assertEqual(metadata["post_census_total"], 3)
        self.assertEqual(metadata["coverage_target_total"], 318)
        self.assertEqual(len(institutions), 320)

        eligible = [
            item
            for item in institutions
            if item["eligibility_status"].startswith("included")
        ]
        excluded = [
            item
            for item in institutions
            if item["eligibility_status"].startswith("excluded")
        ]
        overlays = [item for item in institutions if item["official_code"].startswith("LAW-")]
        self.assertEqual(len(eligible), 318)
        self.assertEqual(len(excluded), 2)
        self.assertEqual(
            {_initials_token(item) for item in excluded}, {"unc", "uniuv"}
        )
        self.assertEqual(
            {item["official_code"] for item in overlays},
            {
                "LAW-15367-IFSPB",
                "LAW-15418-UNIND",
                "LAW-15457-UFESPORTE",
            },
        )
        self.assertTrue(all(item["sources"] == [] for item in overlays))
        self.assertTrue(
            all(item["current_situation"] == "created_pending_implementation" for item in overlays)
        )

    def test_every_census_code_has_one_regional_entry(self) -> None:
        base = _read_json(loader.BASE_CATALOG_PATH)
        expected_codes = {item["official_code"] for item in base["institutions"]}
        actual_codes: list[str] = []
        for region, filename in loader.REGION_MANIFESTS.items():
            manifest = _read_json(loader.SOURCES_DIR / filename)
            self.assertEqual(manifest["region"], region)
            actual_codes.extend(item["official_code"] for item in manifest["institutions"])
        self.assertEqual(len(actual_codes), 317)
        self.assertEqual(set(actual_codes), expected_codes)
        self.assertEqual(len(actual_codes), len(set(actual_codes)))

    def test_center_west_research_counts_and_inactive_sources(self) -> None:
        manifest = _read_json(loader.SOURCES_DIR / "center_west.json")
        self.assertEqual(len(manifest["institutions"]), 27)
        self.assertEqual(
            Counter(item["coverage_status"] for item in manifest["institutions"]),
            Counter({"verified": 14, "partial": 9, "manual_review": 4}),
        )
        sources = [
            source
            for institution in manifest["institutions"]
            for source in institution["sources"]
        ]
        self.assertEqual(len(sources), 27)
        self.assertTrue(all(source["is_active"] is False for source in sources))
        self.assertTrue(all(source["http_status"] == 200 for source in sources))
        self.assertTrue(all(source["page_title"] for source in sources))
        self.assertTrue(all(source["verification_evidence"] for source in sources))

    def test_northeast_builder_contract(self) -> None:
        manifest = _read_json(loader.SOURCES_DIR / "northeast.json")
        self.assertEqual(len(manifest["institutions"]), 66)
        counts = Counter(item["coverage_status"] for item in manifest["institutions"])
        self.assertEqual(counts["source_not_found"], 20)
        self.assertEqual(counts["partial"], 46)
        self.assertNotIn("verified", counts)
        self.assertTrue(
            all(
                source["is_active"] is False
                for institution in manifest["institutions"]
                for source in institution["sources"]
            )
        )

    def test_every_source_has_unique_id_and_valid_normalized_url(self) -> None:
        catalog = loader.load_national_catalog()
        source_ids: list[str] = []
        manual_review_seen = False
        for institution in catalog["institutions"]:
            normalized_within_institution: set[str] = set()
            for source in institution["sources"]:
                source_ids.append(source["catalog_source_id"])
                normalized = normalize_url(source["url"])
                self.assertEqual(source["url"], normalized)
                self.assertNotIn(normalized, normalized_within_institution)
                normalized_within_institution.add(normalized)
                self.assertFalse(source["is_active"])
                manual_review_seen = manual_review_seen or source["status"] == "manual_review"
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertTrue(manual_review_seen)

    def test_region_filter_keeps_auditable_metadata(self) -> None:
        catalog = loader.load_national_catalog(regions=["Centro-Oeste"])
        self.assertTrue(
            all(item["region"] == "Centro-Oeste" for item in catalog["institutions"])
        )
        self.assertEqual(catalog["metadata"]["raw_total"], 317)
        self.assertEqual(catalog["metadata"]["coverage_target_total"], 318)
        self.assertEqual(
            catalog["metadata"]["selected_coverage_target_total"], 29
        )

    def test_status_allowlist_accepts_unsupported(self) -> None:
        with _temporary_catalog() as paths:
            center = _read_json(paths.sources / "center_west.json")
            center["institutions"][0]["coverage_status"] = "unsupported"
            center["institutions"][0]["sources"][0]["status"] = "unsupported"
            _write_json(paths.sources / "center_west.json", center)
            with _patched_catalog_paths(paths):
                catalog = loader.load_national_catalog(regions="Centro-Oeste")
            changed = next(
                item for item in catalog["institutions"] if item["official_code"] == "1"
            )
            self.assertEqual(changed["coverage_status"], "unsupported")
            self.assertEqual(changed["sources"][0]["status"], "unsupported")

    def test_invalid_status_is_rejected(self) -> None:
        with _temporary_catalog() as paths:
            center = _read_json(paths.sources / "center_west.json")
            center["institutions"][0]["sources"][0]["status"] = "invented"
            _write_json(paths.sources / "center_west.json", center)
            with _patched_catalog_paths(paths):
                with self.assertRaisesRegex(loader.CatalogValidationError, "unsupported status"):
                    loader.load_national_catalog()

    def test_duplicate_source_id_and_url_are_rejected(self) -> None:
        with _temporary_catalog() as paths:
            center = _read_json(paths.sources / "center_west.json")
            duplicated = copy.deepcopy(center["institutions"][0]["sources"][0])
            duplicated["catalog_source_id"] = "different-id-same-url"
            duplicated["url"] += "/"
            center["institutions"][0]["sources"].append(duplicated)
            _write_json(paths.sources / "center_west.json", center)
            with _patched_catalog_paths(paths):
                with self.assertRaisesRegex(loader.CatalogValidationError, "duplicate normalized source URL"):
                    loader.load_national_catalog()

        with _temporary_catalog() as paths:
            center = _read_json(paths.sources / "center_west.json")
            center["institutions"][1]["sources"][0]["catalog_source_id"] = center[
                "institutions"
            ][0]["sources"][0]["catalog_source_id"]
            _write_json(paths.sources / "center_west.json", center)
            with _patched_catalog_paths(paths):
                with self.assertRaisesRegex(loader.CatalogValidationError, "duplicate catalog_source_id"):
                    loader.load_national_catalog()


    def test_priority_accepts_only_integers_from_one_to_three(self) -> None:
        for valid in (1, 2, 3):
            with self.subTest(valid=valid), _temporary_catalog() as paths:
                center = _read_json(paths.sources / "center_west.json")
                expected_code = center["institutions"][0]["official_code"]
                center["institutions"][0]["sources"][0]["priority"] = valid
                _write_json(paths.sources / "center_west.json", center)

                with _patched_catalog_paths(paths):
                    catalog = loader.load_national_catalog(
                        regions="Centro-Oeste"
                    )

                institution = next(
                    item
                    for item in catalog["institutions"]
                    if item["official_code"] == expected_code
                )
                self.assertEqual(
                    institution["sources"][0]["priority"],
                    valid,
                )

        for invalid in (None, 0, 4, "1", True):
            with self.subTest(invalid=invalid), _temporary_catalog() as paths:
                center = _read_json(paths.sources / "center_west.json")
                center["institutions"][0]["sources"][0]["priority"] = invalid
                _write_json(paths.sources / "center_west.json", center)

                with _patched_catalog_paths(paths):
                    with self.assertRaisesRegex(
                        loader.CatalogValidationError,
                        (
                            r"institution .* source\[0\]\.priority "
                            r"must be an integer from 1 to 3"
                        ),
                    ):
                        loader.load_national_catalog()


class URLNormalizationTest(unittest.TestCase):
    def test_normalization_contract(self) -> None:
        self.assertEqual(
            normalize_url("HTTPS://Example.COM:443/editais/#fragment"),
            "https://example.com/editais",
        )
        self.assertEqual(
            normalize_url("http://Example.COM:80/?page=2#top"),
            "http://example.com?page=2",
        )
        self.assertEqual(
            normalize_url("https://EXAMPLE.com/path/?a=1&b=2"),
            "https://example.com/path?a=1&b=2",
        )

    def test_invalid_urls_fail_clearly(self) -> None:
        for value in ["", "ftp://example.com/editais", "https:///missing-host", "not-a-url"]:
            with self.subTest(value=value):
                with self.assertRaises(URLNormalizationError):
                    normalize_url(value)


def _initials_token(item: dict[str, object]) -> str:
    value = str(item.get("official_initials") or item.get("initials") or "")
    return "".join(character for character in value.casefold() if character.isalnum())


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


class _Paths:
    def __init__(self, root: Path) -> None:
        self.base = root / "institutions_2024.json"
        self.post = root / "post_census_2024.json"
        self.sources = root / "sources"


class _temporary_catalog:
    def __init__(self) -> None:
        self._temporary: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> _Paths:
        self._temporary = tempfile.TemporaryDirectory()
        paths = _Paths(Path(self._temporary.name))
        paths.sources.mkdir()
        paths.base.write_bytes(loader.BASE_CATALOG_PATH.read_bytes())
        paths.post.write_bytes(loader.POST_CENSUS_PATH.read_bytes())
        for filename in loader.REGION_MANIFESTS.values():
            (paths.sources / filename).write_bytes((loader.SOURCES_DIR / filename).read_bytes())
        return paths

    def __exit__(self, *args: object) -> None:
        assert self._temporary is not None
        self._temporary.cleanup()


def _patched_catalog_paths(paths: _Paths):
    return patch.multiple(
        loader,
        BASE_CATALOG_PATH=paths.base,
        POST_CENSUS_PATH=paths.post,
        SOURCES_DIR=paths.sources,
    )


if __name__ == "__main__":
    unittest.main()