from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.catalog.loader import load_national_catalog
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.schemas.coverage import (
    CoverageBreakdown,
    CoverageBreakdownItem,
    CoverageInstitutionItem,
    CoverageInstitutionList,
    CoveragePendingItem,
    CoverageResponse,
    CoverageStage,
    InventoryCoverage,
    SpiderBreakdownItem,
)


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _normalized(value: Any) -> str:
    return _text(value).casefold()


def _percent(count: int, total: int) -> float:
    return round((count * 100.0 / total), 2) if total else 0.0


def _is_eligible(institution: Dict[str, Any]) -> bool:
    return _normalized(institution.get("eligibility_status")).startswith("included")


def _is_census(institution: Dict[str, Any]) -> bool:
    return institution.get("official_code_origin") != "post_census_law"


def _source_statuses(institution: Dict[str, Any], *, include_coverage: bool) -> set[str]:
    statuses = {
        _normalized(source.get("status"))
        for source in (institution.get("sources") or [])
        if _normalized(source.get("status"))
    }
    if include_coverage:
        coverage_status = _normalized(institution.get("coverage_status"))
        if coverage_status:
            statuses.add(coverage_status)
    return statuses


def _matches_catalog_filters(
    institution: Dict[str, Any],
    *,
    region: Optional[str] = None,
    state: Optional[str] = None,
    administrative_category_code: Optional[int] = None,
    academic_organization_code: Optional[int] = None,
    eligibility_status: Optional[str] = None,
    coverage_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    source_status: Optional[str] = None,
) -> bool:
    if region and _normalized(institution.get("region")) != _normalized(region):
        return False
    if state and _normalized(institution.get("state")) != _normalized(state):
        return False
    if administrative_category_code is not None:
        try:
            actual_category = int(institution.get("administrative_category_code"))
        except (TypeError, ValueError):
            return False
        if actual_category != administrative_category_code:
            return False
    if academic_organization_code is not None:
        try:
            actual_organization = int(institution.get("academic_organization_code"))
        except (TypeError, ValueError):
            return False
        if actual_organization != academic_organization_code:
            return False
    if eligibility_status and _normalized(
        institution.get("eligibility_status")
    ) != _normalized(eligibility_status):
        return False
    if coverage_status and _normalized(
        institution.get("coverage_status")
    ) != _normalized(coverage_status):
        return False
    if verification_status and _normalized(verification_status) not in _source_statuses(
        institution, include_coverage=False
    ):
        return False
    if source_status and _normalized(source_status) not in _source_statuses(
        institution, include_coverage=True
    ):
        return False
    return True


def _database_indexes(
    db: Session,
    catalog_institutions: Iterable[Dict[str, Any]],
) -> Tuple[
    Dict[str, Institution],
    Dict[Tuple[str, str, str], Institution],
    Dict[Tuple[str, str], Institution],
    Dict[Tuple[str, str], Institution],
    Dict[int, List[MonitoredSource]],
]:
    catalog_items = list(catalog_institutions)
    catalog_identity_counts = Counter(
        (
            _normalized(item.get("initials")),
            _normalized(item.get("state")),
            _normalized(item.get("official_name")),
        )
        for item in catalog_items
        if _normalized(item.get("initials"))
        and _normalized(item.get("official_name"))
    )
    catalog_initials_counts = Counter(
        (
            _normalized(item.get("initials")),
            _normalized(item.get("state")),
        )
        for item in catalog_items
        if _normalized(item.get("initials"))
    )
    catalog_name_counts = Counter(
        (
            _normalized(item.get("official_name")),
            _normalized(item.get("state")),
        )
        for item in catalog_items
        if _normalized(item.get("official_name"))
    )

    institutions = db.query(Institution).all()
    sources = db.query(MonitoredSource).all()
    by_code: Dict[str, Institution] = {}
    identity_candidates: Dict[
        Tuple[str, str, str], List[Institution]
    ] = defaultdict(list)
    initials_candidates: Dict[
        Tuple[str, str], List[Institution]
    ] = defaultdict(list)
    name_candidates: Dict[Tuple[str, str], List[Institution]] = defaultdict(list)
    sources_by_institution: Dict[int, List[MonitoredSource]] = defaultdict(list)

    for institution in institutions:
        official_code = _text(getattr(institution, "official_code", None))
        if official_code:
            by_code[official_code] = institution
            continue
        state = _normalized(getattr(institution, "state", None))
        initials = _normalized(getattr(institution, "initials", None))
        name = _normalized(getattr(institution, "name", None))
        if initials and name:
            identity_candidates[(initials, state, name)].append(institution)
        if initials:
            initials_candidates[(initials, state)].append(institution)
        if name:
            name_candidates[(name, state)].append(institution)

    by_identity = {
        key: candidates[0]
        for key, candidates in identity_candidates.items()
        if len(candidates) == 1 and catalog_identity_counts[key] == 1
    }
    by_initials = {
        key: candidates[0]
        for key, candidates in initials_candidates.items()
        if len(candidates) == 1 and catalog_initials_counts[key] == 1
    }
    by_name = {
        key: candidates[0]
        for key, candidates in name_candidates.items()
        if len(candidates) == 1 and catalog_name_counts[key] == 1
    }

    for source in sources:
        sources_by_institution[source.institution_id].append(source)
    return by_code, by_identity, by_initials, by_name, sources_by_institution


def _find_database_institution(
    institution: Dict[str, Any],
    by_code: Dict[str, Institution],
    by_identity: Dict[Tuple[str, str, str], Institution],
    by_initials: Dict[Tuple[str, str], Institution],
    by_name: Dict[Tuple[str, str], Institution],
) -> Optional[Institution]:
    official_code = _text(institution.get("official_code"))
    if official_code and official_code in by_code:
        return by_code[official_code]
    state = _normalized(institution.get("state"))
    initials = _normalized(institution.get("initials"))
    name = _normalized(institution.get("official_name"))
    identity_key = (initials, state, name)
    if initials and name and identity_key in by_identity:
        return by_identity[identity_key]
    initials_key = (initials, state)
    if initials and initials_key in by_initials:
        return by_initials[initials_key]
    return by_name.get((name, state))


def _utc_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _is_recently_active(source: MonitoredSource, now: datetime) -> bool:
    if not bool(getattr(source, "is_active", False)):
        return False
    last_success = _utc_datetime(getattr(source, "last_success_at", None))
    if last_success is None:
        return False
    try:
        frequency = int(getattr(source, "check_frequency_minutes", 1440) or 1440)
    except (TypeError, ValueError):
        frequency = 1440
    freshness_minutes = max(2 * max(frequency, 1), 1440)
    return last_success >= now - timedelta(minutes=freshness_minutes)


def _make_record(
    institution: Dict[str, Any],
    *,
    by_code: Dict[str, Institution],
    by_identity: Dict[Tuple[str, str, str], Institution],
    by_initials: Dict[Tuple[str, str], Institution],
    by_name: Dict[Tuple[str, str], Institution],
    db_sources: Dict[int, List[MonitoredSource]],
    claimed_database_ids: set[int],
    now: datetime,
) -> Dict[str, Any]:
    database_institution = _find_database_institution(
        institution,
        by_code,
        by_identity,
        by_initials,
        by_name,
    )
    if database_institution is not None:
        if database_institution.id in claimed_database_ids:
            database_institution = None
        else:
            claimed_database_ids.add(database_institution.id)
    persisted_sources = (
        list(db_sources.get(database_institution.id, []))
        if database_institution is not None
        else []
    )
    catalog_sources = list(institution.get("sources") or [])
    verified = any(
        _normalized(source.get("status")) == "verified"
        for source in catalog_sources
    )
    capture_validated = any(
        bool(source.get("capture_validated_at")) for source in catalog_sources
    ) or any(
        bool(getattr(source, "capture_validated_at", None))
        for source in persisted_sources
    )
    active_monitoring = any(
        _is_recently_active(source, now) for source in persisted_sources
    )
    return {
        "institution": institution,
        "database_institution": database_institution,
        "persisted_sources": persisted_sources,
        "eligible": _is_eligible(institution),
        "registered": database_institution is not None,
        "mapped": bool(catalog_sources),
        "mapped_sources": len(catalog_sources),
        "verified": verified,
        "capture_validated": capture_validated,
        "active_monitoring": active_monitoring,
        "source_active": any(
            bool(getattr(source, "is_active", False)) for source in persisted_sources
        ),
    }


def _metric_breakdown(
    records: Iterable[Dict[str, Any]],
    key_name: str,
    label_name: Optional[str] = None,
) -> List[CoverageBreakdownItem]:
    groups: Dict[str, Dict[str, Any]] = {}
    for record in records:
        institution = record["institution"]
        key = _text(institution.get(key_name)) or "unknown"
        label = _text(institution.get(label_name)) if label_name else key
        if not label:
            label = "Não informado"
        group = groups.setdefault(
            key,
            {
                "key": key,
                "label": label,
                "inventory_total": 0,
                "eligible_total": 0,
                "mapped_sources": 0,
                "institutions_with_source": 0,
                "institutions_without_source": 0,
                "verified": 0,
                "partial": 0,
                "manual_review": 0,
                "source_not_found": 0,
                "capture_validated": 0,
                "active_monitoring": 0,
            },
        )
        group["inventory_total"] += 1
        if not record["eligible"]:
            continue
        group["eligible_total"] += 1
        group["mapped_sources"] += record["mapped_sources"]
        group["institutions_with_source"] += int(record["mapped"])
        group["institutions_without_source"] += int(not record["mapped"])
        group["verified"] += int(record["verified"])
        status = _normalized(institution.get("coverage_status"))
        for status_name in ("partial", "manual_review", "source_not_found"):
            group[status_name] += int(status == status_name)
        group["capture_validated"] += int(record["capture_validated"])
        group["active_monitoring"] += int(record["active_monitoring"])
    return [
        CoverageBreakdownItem(**groups[key])
        for key in sorted(groups, key=str.casefold)
    ]


def _spider_breakdown(records: Iterable[Dict[str, Any]]) -> List[SpiderBreakdownItem]:
    groups: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if not record["eligible"]:
            continue
        institution_code = _text(record["institution"].get("official_code"))
        for source in record["institution"].get("sources") or []:
            spider = _text(source.get("recommended_spider")) or "unknown"
            group = groups.setdefault(spider, {"sources": 0, "institutions": set()})
            group["sources"] += 1
            group["institutions"].add(institution_code)
    return [
        SpiderBreakdownItem(
            spider=spider,
            sources=groups[spider]["sources"],
            institutions=len(groups[spider]["institutions"]),
        )
        for spider in sorted(groups, key=str.casefold)
    ]


def _audit_date(catalog: Dict[str, Any], institutions: Iterable[Dict[str, Any]]) -> Optional[str]:
    values: List[Any] = []
    metadata = catalog.get("metadata") or {}
    for key, value in metadata.items():
        normalized_key = _normalized(key)
        if "audit" in normalized_key or "verified" in normalized_key:
            values.append(value)
    for institution in institutions:
        for source in institution.get("sources") or []:
            values.append(source.get("last_verified_at"))

    dates: List[str] = []
    for value in values:
        if isinstance(value, datetime):
            dates.append(value.date().isoformat())
        elif isinstance(value, date):
            dates.append(value.isoformat())
        else:
            text_value = _text(value)
            if (
                len(text_value) >= 10
                and text_value[4:5] == "-"
                and text_value[7:8] == "-"
            ):
                dates.append(text_value[:10])
    return max(dates) if dates else None


def _records_for_catalog(
    db: Session,
    institutions: Iterable[Dict[str, Any]],
    now: Optional[datetime],
    *,
    catalog_universe: Optional[Iterable[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    catalog_institutions = list(institutions)
    uniqueness_universe = (
        list(catalog_universe)
        if catalog_universe is not None
        else catalog_institutions
    )
    (
        by_code,
        by_identity,
        by_initials,
        by_name,
        db_sources,
    ) = _database_indexes(db, uniqueness_universe)
    current_time = _utc_datetime(now) if now is not None else datetime.now(timezone.utc)
    assert current_time is not None
    claimed_database_ids: set[int] = set()
    return [
        _make_record(
            institution,
            by_code=by_code,
            by_identity=by_identity,
            by_initials=by_initials,
            by_name=by_name,
            db_sources=db_sources,
            claimed_database_ids=claimed_database_ids,
            now=current_time,
        )
        for institution in catalog_institutions
    ]


def build_coverage_report(
    db: Session,
    *,
    region: Optional[str] = None,
    state: Optional[str] = None,
    administrative_category_code: Optional[int] = None,
    source_status: Optional[str] = None,
    now: Optional[datetime] = None,
) -> CoverageResponse:
    catalog = load_national_catalog()
    raw_institutions = list(catalog.get("institutions") or [])
    scoped = [
        institution
        for institution in raw_institutions
        if _matches_catalog_filters(
            institution,
            region=region,
            state=state,
            administrative_category_code=administrative_category_code,
            source_status=source_status,
        )
    ]
    records = _records_for_catalog(
        db,
        scoped,
        now,
        catalog_universe=raw_institutions,
    )
    eligible_records = [record for record in records if record["eligible"]]
    denominator = len(eligible_records)
    registered = sum(int(record["registered"]) for record in eligible_records)

    def stage(metric: str) -> CoverageStage:
        count = sum(int(record[metric]) for record in eligible_records)
        return CoverageStage(institutions=count, percent=_percent(count, denominator))

    institution_status_counts = Counter(
        _text(record["institution"].get("coverage_status")) or "unknown"
        for record in eligible_records
    )
    source_status_counts = Counter(
        _text(source.get("status")) or "unknown"
        for record in eligible_records
        for source in (record["institution"].get("sources") or [])
    )
    mapped_source_total_inventory = sum(
        record["mapped_sources"] for record in records
    )
    mapped_source_total_eligible = sum(
        record["mapped_sources"] for record in eligible_records
    )
    institutions_with_source = sum(int(record["mapped"]) for record in eligible_records)
    institutions_without_source = denominator - institutions_with_source
    verified_source_institutions = sum(
        int(record["verified"]) for record in eligible_records
    )
    partial_source_institutions = institution_status_counts.get("partial", 0)
    manual_review_institutions = institution_status_counts.get("manual_review", 0)
    source_not_found_institutions = institution_status_counts.get(
        "source_not_found", 0
    )
    validated_capture_total = sum(
        int(record["capture_validated"]) for record in eligible_records
    )
    active_monitoring_total = sum(
        int(record["active_monitoring"]) for record in eligible_records
    )

    pending: List[CoveragePendingItem] = []
    for record in eligible_records:
        institution = record["institution"]
        status = _text(institution.get("coverage_status")) or "manual_review"
        if status == "verified" and record["verified"]:
            continue
        reason = _text(institution.get("coverage_notes"))
        if not reason:
            reason = (
                "Nenhuma fonte oficial mapeada."
                if not record["mapped"]
                else "A fonte mapeada ainda não possui verificação integral."
            )
        pending.append(
            CoveragePendingItem(
                official_code=_text(institution.get("official_code")),
                official_name=_text(institution.get("official_name")),
                state=_text(institution.get("state")),
                region=_text(institution.get("region")),
                status=status,
                reason=reason,
            )
        )
    pending.sort(
        key=lambda item: (
            item.region,
            item.state,
            item.official_name,
            item.official_code,
        )
    )

    census_records = [record for record in records if _is_census(record["institution"])]
    eligible_census_total = sum(
        int(record["eligible"]) for record in census_records
    )
    post_census_total = sum(
        int(not _is_census(record["institution"])) for record in records
    )

    return CoverageResponse(
        inventory_total=len(records),
        eligible_target_total=denominator,
        mapped_source_total_inventory=mapped_source_total_inventory,
        mapped_source_total_eligible=mapped_source_total_eligible,
        institutions_with_source=institutions_with_source,
        institutions_without_source=institutions_without_source,
        verified_source_institutions=verified_source_institutions,
        partial_source_institutions=partial_source_institutions,
        manual_review_institutions=manual_review_institutions,
        source_not_found_institutions=source_not_found_institutions,
        validated_capture_total=validated_capture_total,
        active_monitoring_total=active_monitoring_total,
        inventory=InventoryCoverage(
            census_raw_total=len(census_records),
            eligible_census_total=eligible_census_total,
            post_census_total=post_census_total,
            inventory_total=len(records),
            eligible_total=denominator,
            registered=registered,
            percent=_percent(registered, denominator),
        ),
        mapped=stage("mapped"),
        verified=stage("verified"),
        capture_validated=stage("capture_validated"),
        active_monitoring=stage("active_monitoring"),
        institution_status_counts=dict(sorted(institution_status_counts.items())),
        source_status_counts=dict(sorted(source_status_counts.items())),
        breakdown=CoverageBreakdown(
            regions=_metric_breakdown(records, "region"),
            states=_metric_breakdown(records, "state"),
            administrative_categories=_metric_breakdown(
                records,
                "administrative_category_code",
                "administrative_category_label",
            ),
            academic_organizations=_metric_breakdown(
                records,
                "academic_organization_code",
                "academic_organization_label",
            ),
            spiders=_spider_breakdown(records),
        ),
        last_audit=_audit_date(catalog, scoped),
        pending=pending,
    )


def list_coverage_institutions(
    db: Session,
    *,
    region: Optional[str] = None,
    state: Optional[str] = None,
    administrative_category_code: Optional[int] = None,
    academic_organization_code: Optional[int] = None,
    eligibility_status: Optional[str] = None,
    coverage_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    institution_active: Optional[bool] = None,
    source_active: Optional[bool] = None,
    has_source: Optional[bool] = None,
    manual_review: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    now: Optional[datetime] = None,
) -> CoverageInstitutionList:
    catalog = load_national_catalog()
    institutions = [
        institution
        for institution in catalog["institutions"]
        if _matches_catalog_filters(
            institution,
            region=region,
            state=state,
            administrative_category_code=administrative_category_code,
            academic_organization_code=academic_organization_code,
            eligibility_status=eligibility_status,
            coverage_status=coverage_status,
            verification_status=verification_status,
        )
    ]
    records = _records_for_catalog(
        db,
        institutions,
        now,
        catalog_universe=catalog["institutions"],
    )
    selected: List[Dict[str, Any]] = []
    for record in records:
        institution = record["institution"]
        database_institution = record["database_institution"]
        actual_institution_active = (
            bool(getattr(database_institution, "is_active", False))
            if database_institution is not None
            else None
        )
        is_manual_review = (
            _normalized(institution.get("coverage_status")) == "manual_review"
            or "manual_review"
            in _normalized(institution.get("eligibility_status"))
            or "manual_review"
            in _source_statuses(institution, include_coverage=False)
        )
        if has_source is not None and record["mapped"] is not has_source:
            continue
        if source_active is not None and record["source_active"] is not source_active:
            continue
        if institution_active is not None and (
            actual_institution_active is None
            or actual_institution_active is not institution_active
        ):
            continue
        if manual_review is not None and is_manual_review is not manual_review:
            continue
        selected.append(
            {
                **record,
                "institution_active_value": actual_institution_active,
            }
        )

    selected.sort(
        key=lambda record: (
            _text(record["institution"].get("region")),
            _text(record["institution"].get("state")),
            _text(record["institution"].get("official_name")).casefold(),
            _text(record["institution"].get("official_code")),
        )
    )
    total = len(selected)
    page = selected[skip : skip + limit]
    items = []
    for record in page:
        institution = record["institution"]
        items.append(
            CoverageInstitutionItem(
                official_code=_text(institution.get("official_code")),
                official_name=_text(institution.get("official_name")),
                initials=_text(institution.get("initials")),
                state=_text(institution.get("state")),
                region=_text(institution.get("region")),
                administrative_category_code=institution.get(
                    "administrative_category_code"
                ),
                administrative_category=institution.get(
                    "administrative_category_label"
                ),
                academic_organization_code=institution.get(
                    "academic_organization_code"
                ),
                academic_organization=institution.get(
                    "academic_organization_label"
                ),
                eligibility_status=_text(institution.get("eligibility_status")),
                eligibility_reason=institution.get("eligibility_reason"),
                coverage_status=_text(institution.get("coverage_status")),
                coverage_notes=institution.get("coverage_notes"),
                source_count=record["mapped_sources"],
                source_statuses=sorted(
                    _source_statuses(institution, include_coverage=False)
                ),
                has_source=record["mapped"],
                registered=record["registered"],
                institution_active=record["institution_active_value"],
                source_active=record["source_active"],
                capture_validated=record["capture_validated"],
                active_monitoring=record["active_monitoring"],
            )
        )
    return CoverageInstitutionList(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


__all__ = ["build_coverage_report", "list_coverage_institutions"]
