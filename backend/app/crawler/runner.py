import re
import unicodedata
from typing import Iterable, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice
from app.models.crawler_run import CrawlerRun
from app.crawler.utils import normalize_title, normalize_url, generate_fingerprint
from app.crawler.spider_factory import get_spider_for_source

logger = logging.getLogger(__name__)

VALID_NOTICE_TYPES = {
    "edital",
    "concurso",
    "processo_seletivo",
    "licitacao",
    "pregao",
    "resultado",
    "retificacao",
    "homologacao",
    "convocacao",
    "bolsa",
}

NOTICE_TYPE_ALIASES = {
    "edital": "edital",
    "concurso": "concurso",
    "processo_seletivo": "processo_seletivo",
    "selecao": "processo_seletivo",
    "seletivo": "processo_seletivo",
    "licitacao": "licitacao",
    "pregao": "pregao",
    "resultado": "resultado",
    "retificacao": "retificacao",
    "homologacao": "homologacao",
    "convocacao": "convocacao",
    "bolsa": "bolsa",
}


def normalize_notice_type(value: Optional[str]) -> str:
    if not value:
        return "edital"

    without_accents = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        char for char in without_accents if not unicodedata.combining(char)
    )
    normalized = re.sub(r"\s+", " ", without_accents.lower().strip())
    normalized = normalized.replace("-", "_").replace(" ", "_")
    normalized = NOTICE_TYPE_ALIASES.get(normalized, normalized)

    if normalized not in VALID_NOTICE_TYPES:
        return "edital"
    return normalized


def persist_crawled_items(db: Session, source: MonitoredSource, raw_items):
    new_items_count = 0

    for item in raw_items:
        title = item.get("title", "")
        url = item.get("url", "")
        dedupe_raw_url = item.get("dedupe_url") or item.get("canonical_url") or url

        norm_title = normalize_title(title)
        display_url = normalize_url(url, source.url)
        norm_url = normalize_url(dedupe_raw_url, source.url)

        if not norm_title or not display_url or not norm_url:
            continue

        fingerprint = generate_fingerprint(source.institution_id, norm_title, norm_url)
        existing_notice = db.query(Notice).filter(
            or_(
                Notice.fingerprint == fingerprint,
                and_(
                    Notice.institution_id == source.institution_id,
                    Notice.normalized_url == norm_url,
                ),
            )
        ).first()

        if existing_notice:
            continue

        new_notice = Notice(
            institution_id=source.institution_id,
            source_id=source.id,
            title=title.strip(),
            normalized_title=norm_title,
            url=display_url,
            normalized_url=norm_url,
            notice_type=normalize_notice_type(item.get("notice_type", "edital")),
            description=item.get("description"),
            publication_date=item.get("publication_date"),
            fingerprint=fingerprint,
            is_active=True,
            detected_at=datetime.now(timezone.utc),
        )
        db.add(new_notice)
        new_items_count += 1

    return new_items_count


def run_source_crawler(db: Session, source: MonitoredSource):
    logger.info(f"Starting crawl for source ID {source.id} ({source.name})")

    run_record = CrawlerRun(
        source_id=source.id,
        status="running",
        started_at=datetime.now(timezone.utc),
        items_found=0,
        new_items=0,
    )
    db.add(run_record)
    db.commit()
    db.refresh(run_record)

    run_record_id = run_record.id
    source_id = source.id
    spider = get_spider_for_source(source)

    try:
        raw_items = spider.run()
        run_record.items_found = len(raw_items)

        new_items_count = persist_crawled_items(db, source, raw_items)
        db.commit()

        run_record.new_items = new_items_count
        run_record.status = "completed"
        run_record.finished_at = datetime.now(timezone.utc)

        source.last_checked_at = datetime.now(timezone.utc)
        source.last_success_at = datetime.now(timezone.utc)
        source.last_error_message = None

        db.commit()
        logger.info(
            f"Successfully crawled source ID {source.id}. "
            f"Found: {run_record.items_found}, New: {run_record.new_items}"
        )
        return {
            "source_id": source.id,
            "spider": spider.__class__.__name__,
            "items": raw_items,
            "items_found": len(raw_items),
            "new_items": new_items_count,
            "failed": False,
            "error_message": None,
        }

    except Exception as e:
        error_message = str(e)
        logger.exception(f"Error crawling source ID {source_id}: {error_message}")
        db.rollback()

        run_record = db.query(CrawlerRun).filter(CrawlerRun.id == run_record_id).first()
        source = db.query(MonitoredSource).filter(MonitoredSource.id == source_id).first()

        if run_record:
            run_record.status = "failed"
            run_record.error_message = error_message
            run_record.finished_at = datetime.now(timezone.utc)

        if source:
            source.last_checked_at = datetime.now(timezone.utc)
            source.last_error_message = error_message

        db.commit()
        return {
            "source_id": source_id,
            "spider": spider.__class__.__name__,
            "items": [],
            "items_found": 0,
            "new_items": 0,
            "failed": True,
            "error_message": error_message,
        }


def run_crawler(db: Session, source_ids: Optional[Iterable[int]] = None):
    """
    Main engine to run crawlers for active sources of active institutions.
    Returns an aggregate summary and keeps processing when one source fails.
    """
    query = db.query(MonitoredSource).join(Institution).filter(
        MonitoredSource.is_active == True,
        Institution.is_active == True
    )

    if source_ids is not None:
        query = query.filter(MonitoredSource.id.in_(list(source_ids)))

    active_sources = query.all()

    summary = {
        "sources_checked": len(active_sources),
        "items_found": 0,
        "new_items": 0,
        "failed_sources": 0,
    }

    logger.info(f"Found {len(active_sources)} active sources to crawl.")

    for source in active_sources:
        result = run_source_crawler(db, source)
        summary["items_found"] += result["items_found"]
        summary["new_items"] += result["new_items"]
        if result["failed"]:
            summary["failed_sources"] += 1

    return summary



