import json
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource

CATALOG_PATH = Path(__file__).resolve().parents[1] / "seeds" / "northeast_institutions.json"


def load_northeast_catalog(path: Optional[Path] = None) -> List[dict]:
    catalog_path = path or CATALOG_PATH
    with catalog_path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def seed_northeast_institutions(db: Session) -> Dict[str, int]:
    """
    Idempotently create/update Northeast public institutions and monitored sources.
    Sources are matched by institution_id + URL, then by declared replacement
    URLs, then by name for backward compatibility with earlier catalogs.
    """
    stats = {
        "institutions_created": 0,
        "institutions_updated": 0,
        "sources_created": 0,
        "sources_updated": 0,
        "sources_replaced": 0,
    }

    for item in load_northeast_catalog():
        initials = item["initials"].strip().upper()
        institution = db.query(Institution).filter(Institution.initials == initials).first()

        if institution:
            institution.name = item["name"]
            institution.state = item["state"]
            institution.official_site_url = item["official_site_url"]
            institution.is_active = True
            stats["institutions_updated"] += 1
        else:
            institution = Institution(
                name=item["name"],
                initials=initials,
                state=item["state"],
                official_site_url=item["official_site_url"],
                is_active=True,
            )
            db.add(institution)
            db.flush()
            stats["institutions_created"] += 1

        for source_item in item.get("sources", []):
            source_url = source_item["url"].strip()
            replace_urls = [url.strip() for url in source_item.get("replaces", []) if url.strip()]
            source = db.query(MonitoredSource).filter(
                MonitoredSource.institution_id == institution.id,
                MonitoredSource.url == source_url,
            ).first()
            replaced_existing = False

            if source:
                replaced_existing = _deactivate_replaced_sources(db, institution.id, source.id, replace_urls)
            else:
                source = _find_replaced_source(db, institution.id, replace_urls)
                replaced_existing = source is not None

            if not source:
                source = db.query(MonitoredSource).filter(
                    MonitoredSource.institution_id == institution.id,
                    MonitoredSource.name == source_item["name"],
                ).first()
                replaced_existing = source is not None and source.url in replace_urls

            if source:
                source.name = source_item["name"]
                source.url = source_url
                source.source_type = source_item.get("source_type", "HTML_STATIC")
                source.check_frequency_minutes = source_item.get("check_frequency_minutes", 1440)
                source.is_active = source_item.get("is_active", True)
                if replaced_existing:
                    stats["sources_replaced"] += 1
                else:
                    stats["sources_updated"] += 1
            else:
                db.add(
                    MonitoredSource(
                        institution_id=institution.id,
                        name=source_item["name"],
                        url=source_url,
                        source_type=source_item.get("source_type", "HTML_STATIC"),
                        check_frequency_minutes=source_item.get("check_frequency_minutes", 1440),
                        is_active=source_item.get("is_active", True),
                    )
                )
                stats["sources_created"] += 1

    db.commit()
    return stats


def _find_replaced_source(db: Session, institution_id: int, replace_urls: List[str]) -> Optional[MonitoredSource]:
    if not replace_urls:
        return None
    return db.query(MonitoredSource).filter(
        MonitoredSource.institution_id == institution_id,
        MonitoredSource.url.in_(replace_urls),
    ).first()


def _deactivate_replaced_sources(db: Session, institution_id: int, active_source_id: int, replace_urls: List[str]) -> bool:
    if not replace_urls:
        return False

    replaced = False
    old_sources = db.query(MonitoredSource).filter(
        MonitoredSource.institution_id == institution_id,
        MonitoredSource.url.in_(replace_urls),
        MonitoredSource.id != active_source_id,
    ).all()
    for old_source in old_sources:
        if old_source.is_active:
            old_source.is_active = False
            replaced = True
    return replaced