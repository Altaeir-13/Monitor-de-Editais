import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

test_db_path = Path(tempfile.gettempdir()) / f"monitor_editais_coverage_{uuid4().hex}.db"
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{test_db_path.as_posix()}",
        "SECRET_KEY": "test-secret-key-for-coverage-tests-123456789",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CRAWLER_SCHEDULER_ENABLED": "false",
    }
)

from fastapi.testclient import TestClient

from app.catalog.loader import load_national_catalog
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.user import User
from app.services.coverage import _records_for_catalog, build_coverage_report
from main import app


def _eligible(institution: dict) -> bool:
    return str(institution.get("eligibility_status", "")).startswith("included")


def _is_census(institution: dict) -> bool:
    return institution.get("official_code_origin") != "post_census_law"


def _has_status(institution: dict, status: str) -> bool:
    source_statuses = {
        source.get("status") for source in institution.get("sources", [])
    }
    source_statuses.add(institution.get("coverage_status"))
    return status in source_statuses


def _new_institution(item: dict) -> Institution:
    kwargs = {
        "name": item["official_name"],
        "initials": item.get("initials") or f"IES-{item['official_code']}",
        "state": item["state"],
        "official_site_url": item.get("official_site_url")
        or f"https://example.invalid/{item['official_code']}",
        "is_active": True,
    }
    optional_values = {
        "official_code": item["official_code"],
        "region": item.get("region"),
        "administrative_category_code": item.get("administrative_category_code"),
        "academic_organization_code": item.get("academic_organization_code"),
        "source_discovery_status": item.get("coverage_status"),
        "source_discovery_notes": item.get("coverage_notes"),
    }
    for key, value in optional_values.items():
        if hasattr(Institution, key):
            kwargs[key] = value
    return Institution(**kwargs)


def _new_source(
    institution: Institution,
    catalog_source: dict,
    *,
    is_active: bool,
    last_success_at: datetime,
    capture_validated_at: datetime | None,
) -> MonitoredSource:
    kwargs = {
        "institution_id": institution.id,
        "name": catalog_source["name"],
        "url": catalog_source["url"],
        "source_type": catalog_source["source_type"],
        "check_frequency_minutes": 60,
        "last_checked_at": last_success_at,
        "last_success_at": last_success_at,
        "is_active": is_active,
    }
    optional_values = {
        "catalog_source_id": catalog_source.get("catalog_source_id"),
        "coverage_status": catalog_source.get("status"),
        "capture_validated_at": capture_validated_at,
    }
    for key, value in optional_values.items():
        if hasattr(MonitoredSource, key):
            kwargs[key] = value
    return MonitoredSource(**kwargs)


catalog = load_national_catalog()
catalog_institutions = catalog["institutions"]
eligible = [item for item in catalog_institutions if _eligible(item)]
verified_candidates = [
    item
    for item in eligible
    if any(source.get("status") == "verified" for source in item.get("sources", []))
]
partial_candidates = [
    item
    for item in eligible
    if item.get("sources")
    and not any(source.get("status") == "verified" for source in item["sources"])
]
assert len(verified_candidates) >= 2
assert partial_candidates
selected = [verified_candidates[0], verified_candidates[1], partial_candidates[0]]

Base.metadata.create_all(bind=engine)
db = SessionLocal()
results: dict[str, bool] = {}
now = datetime.now(timezone.utc)

try:
    clean_report = build_coverage_report(db)
    results["00_clean_catalog_has_no_operational_claim"] = (
        clean_report.validated_capture_total == 0
        and clean_report.active_monitoring_total == 0
    )

    admin = User(
        name="Coverage Admin",
        email="coverage-admin@example.com",
        password_hash=get_password_hash("SenhaForte123"),
        role="admin",
        is_active=True,
    )
    regular = User(
        name="Coverage User",
        email="coverage-user@example.com",
        password_hash=get_password_hash("SenhaForte123"),
        role="user",
        is_active=True,
    )
    db.add_all([admin, regular])
    db.flush()

    persisted = []
    for item in selected:
        institution = _new_institution(item)
        db.add(institution)
        db.flush()
        persisted.append(institution)

    ambiguous_legacy = Institution(
        name="Registro legado FATEC sem campus identificado",
        initials="FATEC",
        state="SP",
        official_site_url="https://legacy.example.org/fatec",
        is_active=True,
    )
    db.add(ambiguous_legacy)

    db.add(
        _new_source(
            persisted[0],
            selected[0]["sources"][0],
            is_active=True,
            last_success_at=now - timedelta(hours=1),
            capture_validated_at=now - timedelta(hours=1),
        )
    )
    db.add(
        _new_source(
            persisted[1],
            selected[1]["sources"][0],
            is_active=False,
            last_success_at=now - timedelta(hours=1),
            capture_validated_at=now - timedelta(hours=1),
        )
    )
    db.add(
        _new_source(
            persisted[2],
            selected[2]["sources"][0],
            is_active=True,
            last_success_at=now - timedelta(days=2),
            capture_validated_at=None,
        )
    )
    db.commit()

    with TestClient(app) as client:
        results["01_requires_authentication"] = (
            client.get("/admin/coverage").status_code == 401
        )

        regular_login = client.post(
            "/auth/login",
            data={"username": regular.email, "password": "SenhaForte123"},
        )
        admin_login = client.post(
            "/auth/login",
            data={"username": admin.email, "password": "SenhaForte123"},
        )
        regular_token = regular_login.json().get("access_token")
        admin_token = admin_login.json().get("access_token")
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        results["02_rejects_non_admin"] = (
            client.get("/admin/coverage", headers=regular_headers).status_code == 403
        )
        results["03_rejects_unknown_source_status"] = (
            client.get(
                "/admin/coverage?source_status=not-a-status", headers=admin_headers
            ).status_code
            == 422
        )
        results["04_category_filter_is_integer"] = (
            client.get(
                "/admin/coverage?administrative_category_code=abc",
                headers=admin_headers,
            ).status_code
            == 422
        )

        response = client.get("/admin/coverage", headers=admin_headers)
        payload = response.json() if response.status_code == 200 else {}
        inventory = payload.get("inventory", {})
        results["05_admin_response"] = response.status_code == 200
        results["06_census_raw_total"] = inventory.get("census_raw_total") == 317
        results["07_inventory_includes_overlays"] = inventory.get("inventory_total") == 320
        results["08_eligible_denominator"] = inventory.get("eligible_total") == 318
        results["09_registered_inventory"] = (
            inventory.get("registered") == 3 and inventory.get("percent") == 0.94
        )
        results["09b_ambiguous_legacy_is_not_reused"] = (
            db.query(Institution).count() == 4
            and inventory.get("registered") == 3
        )
        fatec_item = next(
            item
            for item in catalog_institutions
            if item.get("official_initials") == "FATEC"
            and item.get("state") == "SP"
        )
        scoped_fatec_record = _records_for_catalog(
            db,
            [fatec_item],
            now,
            catalog_universe=catalog_institutions,
        )[0]
        results["09c_scoped_report_keeps_global_uniqueness"] = (
            scoped_fatec_record["registered"] is False
        )

        expected_mapped = sum(bool(item.get("sources")) for item in eligible)
        expected_verified = sum(
            any(source.get("status") == "verified" for source in item.get("sources", []))
            for item in eligible
        )
        manifest_captured = {
            item["official_code"]
            for item in eligible
            if any(source.get("capture_validated_at") for source in item.get("sources", []))
        }
        expected_captured = len(
            manifest_captured | {selected[0]["official_code"], selected[1]["official_code"]}
        )
        results["10_mapped_uses_manifest_sources"] = (
            payload.get("mapped", {}).get("institutions") == expected_mapped
        )
        results["11_verified_is_separate"] = (
            payload.get("verified", {}).get("institutions") == expected_verified
        )
        results["12_capture_manifest_or_database"] = (
            payload.get("capture_validated", {}).get("institutions") == expected_captured
        )
        results["13_active_requires_recent_success"] = (
            payload.get("active_monitoring", {}).get("institutions") == 1
        )
        stage_counts = {
            inventory.get("registered"),
            payload.get("mapped", {}).get("institutions"),
            payload.get("verified", {}).get("institutions"),
            payload.get("capture_validated", {}).get("institutions"),
            payload.get("active_monitoring", {}).get("institutions"),
        }
        results["14_five_metrics_are_distinct"] = len(stage_counts) == 5
        results["15_status_counts_use_eligible_denominator"] = (
            sum(payload.get("institution_status_counts", {}).values()) == 318
        )
        results["16_academic_breakdown_present"] = bool(
            payload.get("breakdown", {}).get("academic_organizations")
        )
        results["17_pending_has_individual_reason"] = bool(payload.get("pending")) and all(
            {"official_code", "official_name", "state", "region", "status", "reason"}
            <= set(item)
            for item in payload["pending"]
        )

        region = selected[0]["region"]
        region_items = [item for item in catalog_institutions if item["region"] == region]
        region_response = client.get(
            "/admin/coverage", params={"region": region}, headers=admin_headers
        )
        region_inventory = region_response.json().get("inventory", {})
        results["18_region_filter"] = (
            region_response.status_code == 200
            and region_inventory.get("census_raw_total")
            == sum(_is_census(item) for item in region_items)
            and region_inventory.get("inventory_total") == len(region_items)
            and region_inventory.get("eligible_total") == sum(_eligible(item) for item in region_items)
        )

        state = selected[0]["state"]
        state_expected = sum(
            _eligible(item) and item["state"] == state for item in catalog_institutions
        )
        state_response = client.get(
            "/admin/coverage", params={"state": state}, headers=admin_headers
        )
        results["19_state_filter"] = (
            state_response.status_code == 200
            and state_response.json()["inventory"]["eligible_total"] == state_expected
        )

        category = int(selected[0]["administrative_category_code"])
        category_expected = sum(
            _eligible(item)
            and int(item["administrative_category_code"]) == category
            for item in catalog_institutions
        )
        category_response = client.get(
            "/admin/coverage",
            params={"administrative_category_code": category},
            headers=admin_headers,
        )
        results["20_category_filter"] = (
            category_response.status_code == 200
            and category_response.json()["inventory"]["eligible_total"] == category_expected
        )

        partial_expected = sum(
            _eligible(item) and _has_status(item, "partial")
            for item in catalog_institutions
        )
        status_response = client.get(
            "/admin/coverage",
            params={"source_status": "partial"},
            headers=admin_headers,
        )
        results["21_source_status_filter"] = (
            status_response.status_code == 200
            and status_response.json()["inventory"]["eligible_total"] == partial_expected
        )

        expected_inventory_sources = sum(
            len(item.get("sources", [])) for item in catalog_institutions
        )
        expected_eligible_sources = sum(
            len(item.get("sources", [])) for item in eligible
        )
        expected_without_source = sum(
            _eligible(item) and not item.get("sources")
            for item in catalog_institutions
        )
        results["22_explicit_totals"] = (
            payload.get("inventory_total") == 320
            and payload.get("eligible_target_total") == 318
            and payload.get("mapped_source_total_inventory")
            == expected_inventory_sources
            and payload.get("mapped_source_total_eligible")
            == expected_eligible_sources
            and payload.get("institutions_without_source")
            == expected_without_source
            and payload.get("validated_capture_total") == expected_captured
            and payload.get("active_monitoring_total") == 1
        )

        regions_response = client.get(
            "/admin/coverage/regions",
            headers=admin_headers,
        )
        regions_payload = (
            regions_response.json()
            if regions_response.status_code == 200
            else []
        )
        results["23_regions_endpoint"] = (
            regions_response.status_code == 200
            and len(regions_payload) == 5
            and sum(item["inventory_total"] for item in regions_payload) == 320
            and sum(item["eligible_total"] for item in regions_payload) == 318
            and sum(item["mapped_sources"] for item in regions_payload) == 302
        )

        institutions_response = client.get(
            "/admin/coverage/institutions",
            params={"limit": 500},
            headers=admin_headers,
        )
        institutions_payload = (
            institutions_response.json()
            if institutions_response.status_code == 200
            else {}
        )
        results["24_institutions_endpoint"] = (
            institutions_response.status_code == 200
            and institutions_payload.get("total") == 320
            and len(institutions_payload.get("items", [])) == 320
        )

        no_source_expected = sum(
            not item.get("sources") for item in catalog_institutions
        )
        no_source_response = client.get(
            "/admin/coverage/institutions",
            params={"has_source": "false", "limit": 500},
            headers=admin_headers,
        )
        results["25_has_source_filter"] = (
            no_source_response.status_code == 200
            and no_source_response.json().get("total") == no_source_expected
        )

        verified_filter_expected = sum(
            any(source.get("status") == "verified" for source in item.get("sources", []))
            for item in catalog_institutions
        )
        verified_filter_response = client.get(
            "/admin/coverage/institutions",
            params={"verification_status": "verified", "limit": 500},
            headers=admin_headers,
        )
        results["26_verification_filter"] = (
            verified_filter_response.status_code == 200
            and verified_filter_response.json().get("total")
            == verified_filter_expected
        )

        active_institution_response = client.get(
            "/admin/coverage/institutions",
            params={"institution_active": "true", "limit": 500},
            headers=admin_headers,
        )
        active_source_response = client.get(
            "/admin/coverage/institutions",
            params={"source_active": "true", "limit": 500},
            headers=admin_headers,
        )
        results["27_operational_filters"] = (
            active_institution_response.status_code == 200
            and active_institution_response.json().get("total") == 3
            and active_source_response.status_code == 200
            and active_source_response.json().get("total") == 2
        )

        results["28_seed_endpoint_requires_admin"] = (
            client.post("/admin/seed-national").status_code == 401
            and client.post(
                "/admin/seed-national",
                headers=regular_headers,
            ).status_code
            == 403
        )
        invalid_seed_response = client.post(
            "/admin/seed-national",
            params={"region": "Região Inexistente"},
            headers=admin_headers,
        )
        results["29_seed_endpoint_rejects_unknown_region"] = (
            invalid_seed_response.status_code == 422
        )

        seed_response = client.post(
            "/admin/seed-national",
            params={"region": "Centro-Oeste"},
            headers=admin_headers,
        )
        results["30_seed_endpoint_admin"] = (
            seed_response.status_code == 200
            and isinstance(seed_response.json().get("institutions_created"), int)
            and isinstance(seed_response.json().get("sources_created"), int)
        )
finally:
    db.close()
    engine.dispose()
    test_db_path.unlink(missing_ok=True)

print(json.dumps(results, indent=2, ensure_ascii=False))
failures = {name: value for name, value in results.items() if value is not True}
assert not failures, failures
