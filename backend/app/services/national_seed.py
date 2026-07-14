"""Transactional, idempotent seed for the auditable national catalog."""

from __future__ import annotations

import json
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any, Iterable

from app.catalog.loader import load_national_catalog
from app.catalog.urls import URLNormalizationError, normalize_url
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource


INSTITUTION_CANONICAL_FIELDS = {
    "official_code": "official_code",
    "official_name": "official_name",
    "official_initials": "official_initials",
    "state": "state",
    "region": "region",
    "headquarters_city": "headquarters_city",
    "municipality_code": "municipality_code",
    "administrative_category_code": "administrative_category_code",
    "administrative_category_label": "administrative_category",
    "academic_organization_code": "academic_organization_code",
    "academic_organization_label": "academic_organization",
    "census_situation": "census_situation",
    "current_situation": "current_situation",
    "eligibility_status": "eligibility_status",
    "eligibility_reason": "eligibility_reason",
    "inventory_source_url": "inventory_source_url",
    "inventory_reference_date": "inventory_reference_date",
    "source_discovery_status": "source_discovery_status",
    "source_discovery_notes": "source_discovery_notes",
}

SOURCE_CANONICAL_FIELDS = {
    "catalog_source_id": "catalog_source_id",
    "name": "name",
    "source_type": "source_type",
    "content_type": "content_type",
    "recommended_spider": "recommended_spider",
    "status": "coverage_status",
    "last_verified_at": "last_verified_at",
    "http_status": "verification_http_status",
    "final_url": "verification_final_url",
    "redirect_chain": "verification_redirect_chain",
    "page_title": "verification_page_title",
    "verification_evidence": "verification_evidence",
    "verification_notes": "verification_notes",
    "priority": "priority",
    "categories": "notice_categories",
    "capture_validated_at": "capture_validated_at",
    "capture_evidence": "capture_evidence",
}


class NationalSeedError(RuntimeError):
    """Raised when database state makes a safe deterministic upsert impossible."""


def _token(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in text if character.isalnum()).casefold()


def _column_python_type(model: type[Any], field: str) -> type[Any] | None:
    attribute = getattr(model, field, None)
    columns = getattr(getattr(attribute, "property", None), "columns", None)
    if not columns:
        return None
    try:
        return columns[0].type.python_type
    except (AttributeError, NotImplementedError):
        return None


def _coerce_value(model: type[Any], field: str, value: Any) -> Any:
    if value is None:
        return None
    python_type = _column_python_type(model, field)
    if isinstance(value, str) and python_type is datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    if isinstance(value, str) and python_type is date:
        return date.fromisoformat(value[:10])
    if isinstance(value, (list, dict)) and python_type is str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def _normalized_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _values_equal(current: Any, expected: Any) -> bool:
    if isinstance(current, datetime) and isinstance(expected, datetime):
        return _normalized_datetime(current) == _normalized_datetime(expected)
    return current == expected


def _set_if_changed(instance: Any, field: str, value: Any) -> bool:
    if not hasattr(instance, field):
        raise NationalSeedError(
            f"{type(instance).__name__} model is missing required field {field!r}"
        )
    coerced = _coerce_value(type(instance), field, value)
    if _values_equal(getattr(instance, field), coerced):
        return False
    setattr(instance, field, coerced)
    return True


def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _safe_normalize(value: Any) -> str | None:
    if _empty(value):
        return None
    try:
        return normalize_url(str(value))
    except URLNormalizationError:
        return None


def _new_stats() -> dict[str, int]:
    actions = ("created", "updated", "ignored", "replaced")
    stats = {action: 0 for action in actions}
    for object_name in ("institutions", "sources"):
        for action in actions:
            stats[f"{object_name}_{action}"] = 0
    stats.update(
        {
            "pending": 0,
            "manual_review": 0,
            "institutions_pending": 0,
            "institutions_manual_review": 0,
        }
    )
    return stats


def _record(stats: dict[str, int], object_name: str, action: str) -> None:
    stats[action] += 1
    stats[f"{object_name}_{action}"] += 1


def _index_existing_institutions(
    existing: list[Institution],
) -> dict[str, Institution]:
    by_code: dict[str, Institution] = {}
    for institution in existing:
        code = str(institution.official_code or "").strip()
        if not code:
            continue
        if code in by_code:
            raise NationalSeedError(f"database has duplicate official_code {code!r}")
        by_code[code] = institution
    return by_code


def _legacy_institution_match(
    catalog: dict[str, Any],
    existing: list[Institution],
    claimed_ids: set[int],
    catalog_initials_counts: Counter[tuple[str, str]],
    catalog_identity_counts: Counter[tuple[str, str, str]],
) -> Institution | None:
    official_initials = catalog.get("official_initials") or catalog.get("initials")
    if not official_initials:
        return None
    expected_initials = _token(official_initials)
    expected_state = str(catalog.get("state") or "").upper()
    expected_name = _token(catalog.get("official_name"))
    initials_key = (expected_initials, expected_state)
    identity_key = (expected_initials, expected_state, expected_name)

    def candidates(*, require_name: bool) -> list[Institution]:
        return [
            institution
            for institution in existing
            if institution.id not in claimed_ids
            and _empty(institution.official_code)
            and str(institution.state or "").upper() == expected_state
            and _token(institution.initials) == expected_initials
            and (
                not require_name
                or _token(institution.name) == expected_name
            )
        ]

    identity_candidates = candidates(require_name=True)
    if identity_candidates:
        if catalog_identity_counts[identity_key] != 1:
            raise NationalSeedError(
                "legacy fallback identity is ambiguous across the selected "
                f"catalog: {official_initials}/{expected_state}/{catalog.get('official_name')}"
            )
        if len(identity_candidates) > 1:
            raise NationalSeedError(
                "legacy fallback identity matched more than one database row: "
                f"{official_initials}/{expected_state}/{catalog.get('official_name')}"
            )
        return identity_candidates[0]

    initials_candidates = candidates(require_name=False)
    if initials_candidates and catalog_initials_counts[initials_key] != 1:
        raise NationalSeedError(
            "legacy fallback initials are ambiguous across the selected catalog: "
            f"{official_initials}/{expected_state}"
        )
    if len(initials_candidates) > 1:
        raise NationalSeedError(
            f"legacy fallback for {official_initials}/{expected_state} is ambiguous"
        )
    return initials_candidates[0] if initials_candidates else None


def _institution_values(item: dict[str, Any]) -> dict[str, Any]:
    return {
        target: item.get(source)
        for source, target in INSTITUTION_CANONICAL_FIELDS.items()
    }


def _create_institution(item: dict[str, Any]) -> Institution:
    institution = Institution()
    for field, value in _institution_values(item).items():
        _set_if_changed(institution, field, value)
    _set_if_changed(institution, "name", item["official_name"])
    _set_if_changed(institution, "initials", item["initials"])
    _set_if_changed(institution, "official_site_url", item.get("official_site_url"))
    institution.logo_url = None
    pending_implementation = (
        item.get("current_situation") == "created_pending_implementation"
    )
    _set_if_changed(institution, "is_active", not pending_implementation)
    return institution


def _update_institution(existing: Institution, item: dict[str, Any]) -> bool:
    changed = False
    for field, value in _institution_values(item).items():
        changed = _set_if_changed(existing, field, value) or changed
    if _empty(existing.official_site_url) and item.get("official_site_url"):
        changed = (
            _set_if_changed(existing, "official_site_url", item["official_site_url"])
            or changed
        )
    # name, initials, logo_url, is_active and a non-empty site are manual fields.
    return changed


def _source_values(item: dict[str, Any]) -> dict[str, Any]:
    normalized_url = normalize_url(str(item["url"]))
    values = {
        target: item.get(source)
        for source, target in SOURCE_CANONICAL_FIELDS.items()
    }
    values["url"] = normalized_url
    values["normalized_url"] = normalized_url
    return values


def _single_source_match(
    candidates: list[MonitoredSource],
    *,
    context: str,
) -> MonitoredSource | None:
    if len(candidates) > 1:
        raise NationalSeedError(f"{context} matched more than one source row")
    return candidates[0] if candidates else None


def _match_source(
    catalog_source: dict[str, Any],
    institution_sources: list[MonitoredSource],
    global_by_catalog_id: dict[str, MonitoredSource],
    claimed_source_ids: set[int],
) -> tuple[MonitoredSource | None, bool]:
    source_id = catalog_source["catalog_source_id"]
    direct = global_by_catalog_id.get(source_id)
    if direct is not None:
        if direct not in institution_sources:
            raise NationalSeedError(
                f"catalog_source_id {source_id!r} belongs to another institution"
            )
        if direct.id in claimed_source_ids:
            raise NationalSeedError(
                f"catalog_source_id {source_id!r} matched more than once"
            )
        return direct, False

    catalog_url = normalize_url(catalog_source["url"])
    exact_url = _single_source_match(
        [
            source
            for source in institution_sources
            if source.id not in claimed_source_ids
            and _safe_normalize(source.normalized_url or source.url) == catalog_url
        ],
        context=f"normalized URL {catalog_url!r}",
    )

    replacements = {
        str(value).strip()
        for value in (catalog_source.get("replaces") or [])
        if str(value).strip()
    }
    replacement_urls = {
        normalized
        for value in replacements
        if (normalized := _safe_normalize(value)) is not None
    }
    replacement_tokens = {
        _token(value)
        for value in replacements
        if _safe_normalize(value) is None
    }
    replacement = _single_source_match(
        [
            source
            for source in institution_sources
            if source.id not in claimed_source_ids
            and (
                str(source.catalog_source_id or "") in replacements
                or _safe_normalize(source.normalized_url or source.url)
                in replacement_urls
                or _token(source.name) in replacement_tokens
            )
        ],
        context=f"explicit replaces rule for {source_id!r}",
    )
    if (
        exact_url is not None
        and replacement is not None
        and exact_url is not replacement
    ):
        raise NationalSeedError(
            f"source {source_id!r} has conflicting URL and replaces matches"
        )
    if replacement is not None:
        return replacement, True
    if exact_url is not None:
        existing_catalog_id = str(exact_url.catalog_source_id or "").strip()
        if existing_catalog_id:
            raise NationalSeedError(
                f"normalized URL {catalog_url!r} already belongs to "
                f"catalog_source_id {existing_catalog_id!r}; add an explicit "
                "replaces rule"
            )
        return exact_url, False
    return None, False


def _create_source(institution_id: int, item: dict[str, Any]) -> MonitoredSource:
    source = MonitoredSource(institution_id=institution_id, is_active=False)
    for field, value in _source_values(item).items():
        _set_if_changed(source, field, value)
    return source


def _update_source(existing: MonitoredSource, item: dict[str, Any]) -> bool:
    changed = False
    for field, value in _source_values(item).items():
        changed = _set_if_changed(existing, field, value) or changed
    # Preserve activation, scheduling cadence, crawler timestamps and errors.
    return changed


def seed_national_catalog(
    db: Any,
    regions: Iterable[str] | str | None = None,
    *,
    include_post_census: bool = True,
) -> dict[str, int]:
    """Upsert included institutions and sources, committing exactly once.

    pending counts included institutions whose catalog coverage is not yet
    verified; manual_review is the corresponding explicit subset.
    """

    stats = _new_stats()
    try:
        catalog = load_national_catalog(
            regions=regions,
            include_post_census=include_post_census,
        )
        eligible: list[dict[str, Any]] = []
        for item in catalog["institutions"]:
            if str(item.get("eligibility_status", "")).startswith("included"):
                eligible.append(item)
                coverage_status = str(item.get("coverage_status") or "")
                if coverage_status != "verified":
                    stats["pending"] += 1
                    stats["institutions_pending"] += 1
                if coverage_status == "manual_review":
                    stats["manual_review"] += 1
                    stats["institutions_manual_review"] += 1
            else:
                _record(stats, "institutions", "ignored")

        catalog_initials_counts: Counter[tuple[str, str]] = Counter(
            (
                _token(item.get("official_initials") or item.get("initials")),
                str(item.get("state") or "").upper(),
            )
            for item in eligible
            if _token(item.get("official_initials") or item.get("initials"))
        )
        catalog_identity_counts: Counter[tuple[str, str, str]] = Counter(
            (
                _token(item.get("official_initials") or item.get("initials")),
                str(item.get("state") or "").upper(),
                _token(item.get("official_name")),
            )
            for item in eligible
            if _token(item.get("official_initials") or item.get("initials"))
        )

        existing_institutions = list(db.query(Institution).all())
        by_code = _index_existing_institutions(existing_institutions)
        claimed_institution_ids: set[int] = set()
        selected_pairs: list[tuple[dict[str, Any], Institution]] = []

        for item in eligible:
            code = str(item["official_code"])
            institution = by_code.get(code)
            if institution is None:
                institution = _legacy_institution_match(
                    item,
                    existing_institutions,
                    claimed_institution_ids,
                    catalog_initials_counts,
                    catalog_identity_counts,
                )

            if institution is None:
                institution = _create_institution(item)
                db.add(institution)
                db.flush()
                existing_institutions.append(institution)
                _record(stats, "institutions", "created")
            else:
                changed = _update_institution(institution, item)
                _record(
                    stats,
                    "institutions",
                    "updated" if changed else "ignored",
                )

            if institution.id is None:
                raise NationalSeedError(
                    f"institution {code} has no primary key after flush"
                )
            if institution.id in claimed_institution_ids:
                raise NationalSeedError(
                    f"institution row matched more than once: {code}"
                )
            claimed_institution_ids.add(institution.id)
            by_code[code] = institution
            selected_pairs.append((item, institution))

        existing_sources = list(db.query(MonitoredSource).all())
        sources_by_institution: dict[int, list[MonitoredSource]] = defaultdict(list)
        global_by_catalog_id: dict[str, MonitoredSource] = {}
        for source in existing_sources:
            sources_by_institution[source.institution_id].append(source)
            source_id = str(source.catalog_source_id or "").strip()
            if source_id:
                if source_id in global_by_catalog_id:
                    raise NationalSeedError(
                        f"database has duplicate catalog_source_id {source_id!r}"
                    )
                global_by_catalog_id[source_id] = source

        claimed_source_ids: set[int] = set()
        for item, institution in selected_pairs:
            institution_sources = sources_by_institution[institution.id]
            for catalog_source in item.get("sources", []):
                source, replaced = _match_source(
                    catalog_source,
                    institution_sources,
                    global_by_catalog_id,
                    claimed_source_ids,
                )
                if source is None:
                    source = _create_source(institution.id, catalog_source)
                    db.add(source)
                    db.flush()
                    institution_sources.append(source)
                    global_by_catalog_id[catalog_source["catalog_source_id"]] = source
                    _record(stats, "sources", "created")
                else:
                    old_catalog_id = str(source.catalog_source_id or "")
                    changed = _update_source(source, catalog_source)
                    if old_catalog_id and (
                        old_catalog_id != catalog_source["catalog_source_id"]
                    ):
                        global_by_catalog_id.pop(old_catalog_id, None)
                    global_by_catalog_id[catalog_source["catalog_source_id"]] = source
                    if replaced:
                        _record(stats, "sources", "replaced")
                    _record(
                        stats,
                        "sources",
                        "updated" if changed else "ignored",
                    )

                if source.id is None:
                    raise NationalSeedError(
                        f"source for {item['official_code']} has no primary key"
                    )
                if source.id in claimed_source_ids:
                    raise NationalSeedError(
                        "source row matched more than once for institution "
                        f"{item['official_code']}"
                    )
                claimed_source_ids.add(source.id)

        db.commit()
        return stats
    except Exception:
        db.rollback()
        raise


__all__ = ["NationalSeedError", "seed_national_catalog"]
