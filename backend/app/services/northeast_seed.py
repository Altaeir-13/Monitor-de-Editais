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
    Sources are matched by institution_id + URL.
    """
    stats = {
        "institutions_created": 0,
        "institutions_updated": 0,
        "sources_created": 0,
        "sources_updated": 0,
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
            source = db.query(MonitoredSource).filter(
                MonitoredSource.institution_id == institution.id,
                MonitoredSource.url == source_url,
            ).first()

            if not source:
                replace_urls = [url.strip() for url in source_item.get("replaces", []) if url.strip()]
                if replace_urls:
                    source = db.query(MonitoredSource).filter(
                        MonitoredSource.institution_id == institution.id,
                        MonitoredSource.url.in_(replace_urls),
                    ).first()

            if not source:
                source = db.query(MonitoredSource).filter(
                    MonitoredSource.institution_id == institution.id,
                    MonitoredSource.name == source_item["name"],
                ).first()

            if source:
                source.name = source_item["name"]
                source.url = source_url
                source.source_type = source_item.get("source_type", "HTML_STATIC")
                source.check_frequency_minutes = source_item.get("check_frequency_minutes", 1440)
                source.is_active = source_item.get("is_active", True)
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