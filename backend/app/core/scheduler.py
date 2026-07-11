import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler

from app.core.config import settings
from app.crawler.runner import run_crawler
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

CRAWLER_JOB_ID = "scheduled_crawler"
_active_scheduler: Optional[BackgroundScheduler] = None


def run_scheduled_crawler() -> None:
    db = SessionLocal()
    try:
        logger.info("Scheduled crawler started")
        summary = run_crawler(db=db)
        logger.info("Scheduled crawler completed: %s", summary)
    except Exception:
        logger.exception("Scheduled crawler failed")
    finally:
        db.close()


def create_crawler_scheduler() -> BackgroundScheduler:
    if settings.CRAWLER_INTERVAL_MINUTES < 1:
        raise ValueError("CRAWLER_INTERVAL_MINUTES must be greater than or equal to 1")

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scheduled_crawler,
        trigger="interval",
        minutes=settings.CRAWLER_INTERVAL_MINUTES,
        id=CRAWLER_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        "Crawler scheduler job registered: id=%s interval_minutes=%s max_instances=1 coalesce=True",
        CRAWLER_JOB_ID,
        settings.CRAWLER_INTERVAL_MINUTES,
    )
    return scheduler


def start_crawler_scheduler() -> Optional[BackgroundScheduler]:
    global _active_scheduler

    if not settings.CRAWLER_SCHEDULER_ENABLED:
        logger.info("Crawler scheduler disabled by configuration")
        return None

    if _active_scheduler and _active_scheduler.running:
        logger.warning("Crawler scheduler already running; startup skipped")
        return _active_scheduler

    scheduler = create_crawler_scheduler()
    scheduler.start()
    _active_scheduler = scheduler
    logger.info(
        "Crawler scheduler started with interval_minutes=%s",
        settings.CRAWLER_INTERVAL_MINUTES,
    )
    return scheduler


def shutdown_crawler_scheduler(scheduler: Optional[BaseScheduler]) -> None:
    global _active_scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Crawler scheduler stopped")

    if scheduler is _active_scheduler or (_active_scheduler and not _active_scheduler.running):
        _active_scheduler = None
