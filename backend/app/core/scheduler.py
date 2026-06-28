import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler

from app.core.config import settings
from app.crawler.runner import run_crawler
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

CRAWLER_JOB_ID = "scheduled_crawler"


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
    return scheduler


def start_crawler_scheduler() -> Optional[BackgroundScheduler]:
    if not settings.CRAWLER_SCHEDULER_ENABLED:
        logger.info("Crawler scheduler disabled by configuration")
        return None

    scheduler = create_crawler_scheduler()
    scheduler.start()
    logger.info(
        "Crawler scheduler started with interval_minutes=%s",
        settings.CRAWLER_INTERVAL_MINUTES,
    )
    return scheduler


def shutdown_crawler_scheduler(scheduler: Optional[BaseScheduler]) -> None:
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Crawler scheduler stopped")