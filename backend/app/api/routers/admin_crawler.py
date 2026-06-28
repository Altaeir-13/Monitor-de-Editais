from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crawler.runner import run_crawler
from app.models.crawler_run import CrawlerRun
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.models.notice import Notice
from app.models.user import User
from app.schemas.crawler_status import (
    CrawlerRunResponse,
    CrawlerSourceStatusResponse,
    CrawlerSourceSummary,
    CrawlerStatusResponse,
)

router = APIRouter()


def _latest_run_for_source(db: Session, source_id: int) -> Optional[CrawlerRun]:
    return (
        db.query(CrawlerRun)
        .filter(CrawlerRun.source_id == source_id)
        .order_by(CrawlerRun.started_at.desc(), CrawlerRun.id.desc())
        .first()
    )


def _run_to_response(run: CrawlerRun) -> CrawlerRunResponse:
    source = run.source
    institution = source.institution
    return CrawlerRunResponse(
        id=run.id,
        source_id=run.source_id,
        source_name=source.name,
        source_url=source.url,
        institution=CrawlerSourceSummary(
            id=institution.id,
            name=institution.name,
            initials=institution.initials,
        ),
        status=run.status,
        items_found=run.items_found or 0,
        new_items=run.new_items or 0,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


def _calculate_health_status(source: MonitoredSource, last_run: Optional[CrawlerRun]) -> str:
    if not source.is_active:
        return "inactive"
    if source.last_checked_at is None and last_run is None:
        return "never_checked"
    if source.last_error_message or (last_run is not None and last_run.status == "failed"):
        return "error"
    if last_run is not None and last_run.status == "completed" and (last_run.items_found or 0) == 0:
        return "warning"
    return "ok"


def _source_status_response(db: Session, source: MonitoredSource) -> CrawlerSourceStatusResponse:
    last_run = _latest_run_for_source(db, source.id)
    health_status = _calculate_health_status(source, last_run)
    institution = source.institution
    return CrawlerSourceStatusResponse(
        source_id=source.id,
        source_name=source.name,
        source_url=source.url,
        source_type=source.source_type,
        institution_id=institution.id,
        institution_name=institution.name,
        institution_initials=institution.initials,
        is_active=source.is_active,
        last_checked_at=source.last_checked_at,
        last_success_at=source.last_success_at,
        last_error_message=source.last_error_message,
        health_status=health_status,
        last_run=_run_to_response(last_run) if last_run else None,
    )


@router.get("/crawler/status", response_model=CrawlerStatusResponse)
def get_crawler_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    sources = db.query(MonitoredSource).join(Institution).all()
    source_statuses = [_source_status_response(db, source) for source in sources]
    status_counts = {status: 0 for status in ["ok", "warning", "error", "never_checked", "inactive"]}
    for source_status in source_statuses:
        status_counts[source_status.health_status] += 1

    last_run = (
        db.query(CrawlerRun)
        .order_by(CrawlerRun.started_at.desc(), CrawlerRun.id.desc())
        .first()
    )

    total_active_notices = db.query(Notice).filter(Notice.is_active == True).count()

    return CrawlerStatusResponse(
        total_sources=len(sources),
        active_sources=sum(1 for source in sources if source.is_active),
        inactive_sources=status_counts["inactive"],
        ok_sources=status_counts["ok"],
        warning_sources=status_counts["warning"],
        error_sources=status_counts["error"],
        never_checked_sources=status_counts["never_checked"],
        total_active_notices=total_active_notices,
        last_run=_run_to_response(last_run) if last_run else None,
        last_run_items_found=(last_run.items_found or 0) if last_run else 0,
        last_run_new_items=(last_run.new_items or 0) if last_run else 0,
    )


@router.get("/crawler/sources-status", response_model=List[CrawlerSourceStatusResponse])
def get_crawler_sources_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    sources = (
        db.query(MonitoredSource)
        .join(Institution)
        .order_by(Institution.initials.asc(), MonitoredSource.name.asc(), MonitoredSource.id.asc())
        .all()
    )
    return [_source_status_response(db, source) for source in sources]


@router.get("/crawler/runs", response_model=List[CrawlerRunResponse])
def get_crawler_runs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    runs = (
        db.query(CrawlerRun)
        .join(MonitoredSource)
        .join(Institution)
        .order_by(CrawlerRun.started_at.desc(), CrawlerRun.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_run_to_response(run) for run in runs]


@router.post("/run-crawler/source/{source_id}")
def trigger_crawler_for_source(
    source_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    source = db.query(MonitoredSource).filter(MonitoredSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="MonitoredSource not found")
    if not source.is_active:
        raise HTTPException(status_code=400, detail="MonitoredSource is inactive")
    return run_crawler(db=db, source_ids=[source_id])
