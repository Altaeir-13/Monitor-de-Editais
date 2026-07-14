"""Strict loader for the national INEP inventory and regional source manifests."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .urls import URLNormalizationError, normalize_url


CATALOG_DIR = Path(__file__).resolve().parent
BASE_CATALOG_PATH = CATALOG_DIR / "institutions_2024.json"
POST_CENSUS_PATH = CATALOG_DIR / "post_census_2024.json"
SOURCES_DIR = CATALOG_DIR / "sources"

REGION_MANIFESTS = {
    "Norte": "north.json",
    "Nordeste": "northeast.json",
    "Centro-Oeste": "center_west.json",
    "Sudeste": "southeast.json",
    "Sul": "south.json",
}

ALLOWED_STATUSES = {
    "verified",
    "partial",
    "source_not_found",
    "temporarily_unavailable",
    "manual_review",
    "unsupported",
    "inactive",
}
ALLOWED_SPIDERS = {"generic", "wordpress", "govbr", "sigaa", "pagination"}
EXPECTED_RAW_TOTAL = 317
EXPECTED_ELIGIBLE_CENSUS_TOTAL = 315
EXPECTED_POST_CENSUS_TOTAL = 3
EXPECTED_COVERAGE_TARGET_TOTAL = 318


class CatalogValidationError(ValueError):
    """Raised when a versioned catalog or manifest violates its contract."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogValidationError(f"catalog file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CatalogValidationError(f"catalog root must be an object: {path}")
    if payload.get("schema_version") != 1:
        raise CatalogValidationError(
            f"unsupported schema_version in {path}: {payload.get('schema_version')!r}"
        )
    return payload


def _required_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogValidationError(f"{context} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any, context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise CatalogValidationError(f"{context} must be a string or null")
    return value.strip() or None


def _normalized_url(value: Any, context: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    try:
        return normalize_url(_required_string(value, context))
    except URLNormalizationError as exc:
        raise CatalogValidationError(f"{context}: {exc}") from exc


def _validate_status(value: Any, context: str) -> str:
    status = _required_string(value, context)
    if status not in ALLOWED_STATUSES:
        raise CatalogValidationError(
            f"{context} has unsupported status {status!r}; "
            f"allowed: {sorted(ALLOWED_STATUSES)}"
        )
    return status


def _validate_string_list(value: Any, context: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise CatalogValidationError(f"{context} must be a list of strings")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_required_string(item, f"{context}[{index}]"))
    if len(result) != len(set(result)):
        raise CatalogValidationError(f"{context} contains duplicate values")
    return result


def _validate_redirect_chain(value: Any, context: str) -> list[str]:
    chain = _validate_string_list(value, context)
    return [
        str(_normalized_url(item, f"{context}[{index}]"))
        for index, item in enumerate(chain)
    ]


def _validate_priority(
    value: Any,
    context: str,
    *,
    optional: bool = False,
) -> int | None:
    if value is None and optional:
        return None

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 3
    ):
        raise CatalogValidationError(
            f"{context} must be an integer from 1 to 3"
        )

    return value


def _validate_replacements(value: Any, context: str) -> list[str]:
    replacements = _validate_string_list(value, context)
    normalized: list[str] = []

    for index, item in enumerate(replacements):
        item_context = f"{context}[{index}]"
        normalized_item = (
            str(_normalized_url(item, item_context))
            if "://" in item
            else item
        )
        normalized.append(normalized_item)

    if len(normalized) != len(set(normalized)):
        raise CatalogValidationError(
            f"{context} contains duplicate normalized values"
        )

    return normalized


def _validate_source(
    raw: Any,
    *,
    institution_code: str,
    source_index: int,
    global_source_ids: set[str],
) -> dict[str, Any]:
    context = f"institution {institution_code} source[{source_index}]"
    if not isinstance(raw, dict):
        raise CatalogValidationError(f"{context} must be an object")

    source = copy.deepcopy(raw)
    source_id = _required_string(source.get("catalog_source_id"), f"{context}.catalog_source_id")
    if source_id in global_source_ids:
        raise CatalogValidationError(f"duplicate catalog_source_id: {source_id}")
    global_source_ids.add(source_id)

    source["catalog_source_id"] = source_id
    source["name"] = _required_string(source.get("name"), f"{context}.name")
    source["url"] = _normalized_url(source.get("url"), f"{context}.url")
    source["source_type"] = _required_string(
        source.get("source_type"), f"{context}.source_type"
    )
    source["content_type"] = _required_string(
        source.get("content_type"), f"{context}.content_type"
    )
    spider = _required_string(
        source.get("recommended_spider"), f"{context}.recommended_spider"
    )
    if spider not in ALLOWED_SPIDERS:
        raise CatalogValidationError(
            f"{context}.recommended_spider has unsupported value {spider!r}; "
            f"allowed: {sorted(ALLOWED_SPIDERS)}"
        )
    source["recommended_spider"] = spider
    source["status"] = _validate_status(source.get("status"), f"{context}.status")

    is_active = source.get("is_active", False)
    if not isinstance(is_active, bool):
        raise CatalogValidationError(f"{context}.is_active must be boolean")
    source["is_active"] = is_active

    source["last_verified_at"] = _optional_string(
        source.get("last_verified_at"), f"{context}.last_verified_at"
    )
    http_status = source.get("http_status")
    if http_status is not None and (
        isinstance(http_status, bool)
        or not isinstance(http_status, int)
        or not 100 <= http_status <= 599
    ):
        raise CatalogValidationError(
            f"{context}.http_status must be an HTTP status integer or null"
        )
    source["http_status"] = http_status
    source["final_url"] = _normalized_url(
        source.get("final_url"), f"{context}.final_url", optional=True
    )
    source["redirect_chain"] = _validate_redirect_chain(
        source.get("redirect_chain", []), f"{context}.redirect_chain"
    )
    source["page_title"] = _optional_string(
        source.get("page_title"), f"{context}.page_title"
    )
    source["verification_evidence"] = _optional_string(
        source.get("verification_evidence"), f"{context}.verification_evidence"
    )
    source["verification_notes"] = _optional_string(
        source.get("verification_notes"), f"{context}.verification_notes"
    )
    source["priority"] = _validate_priority(
        source.get("priority"),
        f"{context}.priority",
    )
    source["categories"] = _validate_string_list(
        source.get("categories", []), f"{context}.categories"
    )
    source["capture_validated_at"] = _optional_string(
        source.get("capture_validated_at"), f"{context}.capture_validated_at"
    )
    source["capture_evidence"] = _optional_string(
        source.get("capture_evidence"), f"{context}.capture_evidence"
    )
    source["replaces"] = _validate_replacements(
        source.get("replaces", []),
        f"{context}.replaces",
    )
    return source


def _load_and_validate_manifests(
    base_by_code: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    entries_by_code: dict[str, dict[str, Any]] = {}
    manifest_verified_at: dict[str, str] = {}
    global_source_ids: set[str] = set()

    for region, filename in REGION_MANIFESTS.items():
        path = SOURCES_DIR / filename
        manifest = _read_json(path)
        if manifest.get("region") != region:
            raise CatalogValidationError(
                f"{path} region must be {region!r}, got {manifest.get('region')!r}"
            )
        verified_at = _required_string(
            manifest.get("verified_at"), f"{path}.verified_at"
        )
        manifest_verified_at[region] = verified_at
        entries = manifest.get("institutions")
        if not isinstance(entries, list):
            raise CatalogValidationError(f"{path}.institutions must be a list")

        for entry_index, raw_entry in enumerate(entries):
            context = f"{path}.institutions[{entry_index}]"
            if not isinstance(raw_entry, dict):
                raise CatalogValidationError(f"{context} must be an object")
            entry = copy.deepcopy(raw_entry)
            code = _required_string(entry.get("official_code"), f"{context}.official_code")
            if not code.isdigit():
                raise CatalogValidationError(f"{context}.official_code must be numeric")
            if code in entries_by_code:
                raise CatalogValidationError(
                    f"institution {code} appears in more than one regional manifest"
                )
            base = base_by_code.get(code)
            if base is None:
                raise CatalogValidationError(
                    f"regional manifest references unknown INEP code {code}"
                )
            if base.get("region") != region:
                raise CatalogValidationError(
                    f"institution {code} belongs to {base.get('region')}, not {region}"
                )

            entry["official_code"] = code
            entry["official_site_url"] = _normalized_url(
                entry.get("official_site_url"),
                f"{context}.official_site_url",
                optional=True,
            )
            entry["coverage_status"] = _validate_status(
                entry.get("coverage_status"), f"{context}.coverage_status"
            )
            entry["coverage_notes"] = _optional_string(
                entry.get("coverage_notes"), f"{context}.coverage_notes"
            )

            if "eligibility_status" in entry:
                eligibility_status = _required_string(
                    entry.get("eligibility_status"), f"{context}.eligibility_status"
                )
                if not (
                    eligibility_status.startswith("included")
                    or eligibility_status.startswith("excluded")
                ):
                    raise CatalogValidationError(
                        f"{context}.eligibility_status must start with included or excluded"
                    )
                entry["eligibility_status"] = eligibility_status
                entry["eligibility_reason"] = _optional_string(
                    entry.get("eligibility_reason"), f"{context}.eligibility_reason"
                )

            raw_sources = entry.get("sources")
            if not isinstance(raw_sources, list):
                raise CatalogValidationError(f"{context}.sources must be a list")
            sources: list[dict[str, Any]] = []
            normalized_urls: set[str] = set()
            for source_index, raw_source in enumerate(raw_sources):
                source = _validate_source(
                    raw_source,
                    institution_code=code,
                    source_index=source_index,
                    global_source_ids=global_source_ids,
                )
                normalized = str(source["url"])
                if normalized in normalized_urls:
                    raise CatalogValidationError(
                        f"institution {code} has duplicate normalized source URL {normalized}"
                    )
                normalized_urls.add(normalized)
                sources.append(source)
            entry["sources"] = sources
            entries_by_code[code] = entry

    missing = sorted(set(base_by_code) - set(entries_by_code), key=int)
    extra = sorted(set(entries_by_code) - set(base_by_code), key=int)
    if missing or extra:
        raise CatalogValidationError(
            "regional manifests must contain exactly one entry for every census code; "
            f"missing={missing}, extra={extra}"
        )
    return entries_by_code, manifest_verified_at


def _merge_census_institutions(
    base_institutions: list[dict[str, Any]],
    manifest_entries: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for raw_base in base_institutions:
        institution = copy.deepcopy(raw_base)
        code = str(institution["official_code"])
        manifest = manifest_entries[code]
        if "eligibility_status" in manifest:
            institution["eligibility_status"] = manifest["eligibility_status"]
            institution["eligibility_reason"] = manifest.get("eligibility_reason")
        institution["official_site_url"] = manifest.get("official_site_url")
        institution["source_discovery_status"] = manifest["coverage_status"]
        institution["source_discovery_notes"] = manifest.get("coverage_notes")
        institution["coverage_status"] = manifest["coverage_status"]
        institution["coverage_notes"] = manifest.get("coverage_notes")
        institution["sources"] = manifest["sources"]
        merged.append(institution)
    return merged


def _validate_post_census(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_institutions = payload.get("institutions")
    if not isinstance(raw_institutions, list):
        raise CatalogValidationError("post_census_2024.json institutions must be a list")
    result: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for index, raw in enumerate(raw_institutions):
        context = f"post_census_2024.json institutions[{index}]"
        if not isinstance(raw, dict):
            raise CatalogValidationError(f"{context} must be an object")
        institution = copy.deepcopy(raw)
        code = _required_string(institution.get("official_code"), f"{context}.official_code")
        if not code.startswith("LAW-"):
            raise CatalogValidationError(f"{context}.official_code must start with LAW-")
        if code in seen_codes:
            raise CatalogValidationError(f"duplicate post-census code {code}")
        seen_codes.add(code)
        if institution.get("official_code_origin") != "post_census_law":
            raise CatalogValidationError(
                f"{context}.official_code_origin must be post_census_law"
            )
        institution["inventory_source_url"] = _normalized_url(
            institution.get("inventory_source_url"), f"{context}.inventory_source_url"
        )
        institution["official_site_url"] = _normalized_url(
            institution.get("official_site_url"),
            f"{context}.official_site_url",
            optional=True,
        )
        institution["coverage_status"] = _validate_status(
            institution.get("coverage_status"), f"{context}.coverage_status"
        )
        eligibility = _required_string(
            institution.get("eligibility_status"), f"{context}.eligibility_status"
        )
        if not eligibility.startswith("included"):
            raise CatalogValidationError(
                f"{context}.eligibility_status must start with included"
            )
        sources = institution.get("sources")
        if sources != []:
            raise CatalogValidationError(f"{context}.sources must be empty until activation")
        result.append(institution)
    if len(result) != EXPECTED_POST_CENSUS_TOTAL:
        raise CatalogValidationError(
            f"expected {EXPECTED_POST_CENSUS_TOTAL} post-census institutions, got {len(result)}"
        )
    return result


def _normalize_regions(regions: Iterable[str] | str | None) -> set[str]:
    if regions is None:
        return set(REGION_MANIFESTS)
    if isinstance(regions, str):
        regions = [regions]
    selected = {_required_string(region, "region") for region in regions}
    unknown = selected - set(REGION_MANIFESTS)
    if unknown:
        raise CatalogValidationError(
            f"unknown regions {sorted(unknown)}; allowed: {sorted(REGION_MANIFESTS)}"
        )
    if not selected:
        raise CatalogValidationError("regions must not be empty")
    return selected


def load_national_catalog(
    regions: Iterable[str] | str | None = None,
    include_post_census: bool = True,
) -> dict[str, Any]:
    """Load, validate and merge the national catalog without accessing the network.

    Excluded inventory rows remain in the returned list for auditability.  Seed
    consumers must select records whose ``eligibility_status`` starts with
    ``included``.
    """

    if not isinstance(include_post_census, bool):
        raise CatalogValidationError("include_post_census must be boolean")
    selected_regions = _normalize_regions(regions)
    base = _read_json(BASE_CATALOG_PATH)
    raw_base_institutions = base.get("institutions")
    if not isinstance(raw_base_institutions, list):
        raise CatalogValidationError("institutions_2024.json institutions must be a list")
    if len(raw_base_institutions) != EXPECTED_RAW_TOTAL:
        raise CatalogValidationError(
            f"expected {EXPECTED_RAW_TOTAL} census institutions, "
            f"got {len(raw_base_institutions)}"
        )
    base_by_code: dict[str, dict[str, Any]] = {}
    for index, institution in enumerate(raw_base_institutions):
        if not isinstance(institution, dict):
            raise CatalogValidationError(f"base institution[{index}] must be an object")
        code = _required_string(
            institution.get("official_code"), f"base institution[{index}].official_code"
        )
        if not code.isdigit() or code in base_by_code:
            raise CatalogValidationError(f"invalid or duplicate census code {code!r}")
        base_by_code[code] = institution

    manifest_entries, manifest_verified_at = _load_and_validate_manifests(base_by_code)
    census_institutions = _merge_census_institutions(
        raw_base_institutions, manifest_entries
    )
    eligible_census_total = sum(
        str(item.get("eligibility_status", "")).startswith("included")
        for item in census_institutions
    )
    if eligible_census_total != EXPECTED_ELIGIBLE_CENSUS_TOTAL:
        raise CatalogValidationError(
            f"expected {EXPECTED_ELIGIBLE_CENSUS_TOTAL} eligible census institutions, "
            f"got {eligible_census_total}"
        )

    post_census = _validate_post_census(_read_json(POST_CENSUS_PATH))
    coverage_target_total = eligible_census_total + sum(
        str(item.get("eligibility_status", "")).startswith("included")
        for item in post_census
    )
    if coverage_target_total != EXPECTED_COVERAGE_TARGET_TOTAL:
        raise CatalogValidationError(
            f"expected coverage target {EXPECTED_COVERAGE_TARGET_TOTAL}, "
            f"got {coverage_target_total}"
        )

    selected_census = [
        item for item in census_institutions if item.get("region") in selected_regions
    ]
    selected_post = (
        [item for item in post_census if item.get("region") in selected_regions]
        if include_post_census
        else []
    )
    institutions = selected_census + selected_post
    institutions.sort(
        key=lambda item: (
            item.get("region", ""),
            item.get("state", ""),
            0 if str(item.get("official_code", "")).isdigit() else 1,
            int(item["official_code"])
            if str(item.get("official_code", "")).isdigit()
            else str(item.get("official_code", "")),
        )
    )

    metadata = copy.deepcopy(base.get("metadata", {}))
    metadata.update(
        {
            "raw_total": EXPECTED_RAW_TOTAL,
            "eligible_census_total": eligible_census_total,
            "post_census_total": len(post_census),
            "coverage_target_total": coverage_target_total,
            "inventory_total_including_excluded_and_post_census": (
                EXPECTED_RAW_TOTAL + len(post_census)
            ),
            "selected_regions": sorted(selected_regions),
            "selected_inventory_total": len(institutions),
            "selected_coverage_target_total": sum(
                str(item.get("eligibility_status", "")).startswith("included")
                for item in institutions
            ),
            "includes_post_census": include_post_census,
            "manifest_verified_at": manifest_verified_at,
        }
    )
    return {"metadata": metadata, "institutions": institutions}


__all__ = [
    "ALLOWED_SPIDERS",
    "ALLOWED_STATUSES",
    "CatalogValidationError",
    "REGION_MANIFESTS",
    "load_national_catalog",
]