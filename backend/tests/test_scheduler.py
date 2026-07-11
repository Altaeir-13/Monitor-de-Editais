import json
import logging
import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core import scheduler as crawler_scheduler


class FakeSession:
    def __init__(self):
        self.closed = False
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakeSessionFactory:
    def __init__(self):
        self.sessions = []

    def __call__(self):
        session = FakeSession()
        self.sessions.append(session)
        return session


def interval_minutes(job) -> int:
    return int(job.trigger.interval.total_seconds() / 60)


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


results = {}

original_enabled = crawler_scheduler.settings.CRAWLER_SCHEDULER_ENABLED
original_interval = crawler_scheduler.settings.CRAWLER_INTERVAL_MINUTES
original_session_local = crawler_scheduler.SessionLocal
original_run_crawler = crawler_scheduler.run_crawler
original_active_scheduler = crawler_scheduler._active_scheduler

handler = ListHandler()
crawler_scheduler.logger.addHandler(handler)
crawler_scheduler.logger.setLevel(logging.INFO)

try:
    crawler_scheduler._active_scheduler = None

    crawler_scheduler.settings.CRAWLER_SCHEDULER_ENABLED = False
    disabled_scheduler = crawler_scheduler.start_crawler_scheduler()
    results["1_disabled_returns_none"] = disabled_scheduler is None
    results["2_disabled_does_not_register_active_scheduler"] = crawler_scheduler._active_scheduler is None

    crawler_scheduler.settings.CRAWLER_SCHEDULER_ENABLED = True
    crawler_scheduler.settings.CRAWLER_INTERVAL_MINUTES = 1
    enabled_scheduler = crawler_scheduler.start_crawler_scheduler()
    try:
        jobs = enabled_scheduler.get_jobs()
        job = enabled_scheduler.get_job(crawler_scheduler.CRAWLER_JOB_ID)
        results["3_enabled_starts_scheduler"] = enabled_scheduler.running is True
        results["4_enabled_registers_one_job"] = len(jobs) == 1
        results["5_job_id_is_stable"] = job.id == crawler_scheduler.CRAWLER_JOB_ID
        results["6_job_interval_uses_config"] = interval_minutes(job) == 1
        results["7_job_prevents_overlap"] = job.max_instances == 1
        results["8_job_coalesces_missed_runs"] = job.coalesce is True

        duplicate_scheduler = crawler_scheduler.start_crawler_scheduler()
        results["9_duplicate_start_returns_same_scheduler"] = duplicate_scheduler is enabled_scheduler
        results["10_duplicate_start_keeps_one_job"] = len(duplicate_scheduler.get_jobs()) == 1
    finally:
        crawler_scheduler.shutdown_crawler_scheduler(enabled_scheduler)

    results["11_shutdown_stops_scheduler"] = enabled_scheduler.running is False
    crawler_scheduler.shutdown_crawler_scheduler(enabled_scheduler)
    results["12_repeated_shutdown_is_safe"] = enabled_scheduler.running is False and crawler_scheduler._active_scheduler is None

    session_factory = FakeSessionFactory()
    crawler_calls = []

    def fake_run_crawler(db):
        crawler_calls.append(db)
        return {"sources_checked": 0, "items_found": 0, "new_items": 0, "failed_sources": 0}

    crawler_scheduler.SessionLocal = session_factory
    crawler_scheduler.run_crawler = fake_run_crawler
    crawler_scheduler.run_scheduled_crawler()
    results["13_job_creates_one_db_session"] = len(session_factory.sessions) == 1
    results["14_job_calls_runner_once"] = len(crawler_calls) == 1 and crawler_calls[0] is session_factory.sessions[0]
    results["15_job_closes_session_on_success"] = session_factory.sessions[0].closed is True
    results["16_job_leaves_transaction_control_to_runner"] = (
        session_factory.sessions[0].commits == 0 and session_factory.sessions[0].rollbacks == 0
    )

    failing_factory = FakeSessionFactory()

    def failing_run_crawler(db):
        raise RuntimeError("simulated crawler failure")

    crawler_scheduler.SessionLocal = failing_factory
    crawler_scheduler.run_crawler = failing_run_crawler
    crawler_scheduler.run_scheduled_crawler()
    results["17_failure_closes_session"] = len(failing_factory.sessions) == 1 and failing_factory.sessions[0].closed is True
    results["18_failure_is_logged"] = any(
        record.levelno >= logging.ERROR and "Scheduled crawler failed" in record.getMessage()
        for record in handler.records
    )
    results["19_failure_does_not_escape_job"] = True

    crawler_scheduler.settings.CRAWLER_SCHEDULER_ENABLED = True
    crawler_scheduler.settings.CRAWLER_INTERVAL_MINUTES = 0
    try:
        crawler_scheduler.create_crawler_scheduler()
        results["20_invalid_interval_rejected"] = False
    except ValueError:
        results["20_invalid_interval_rejected"] = True
finally:
    active_scheduler = crawler_scheduler._active_scheduler
    if active_scheduler and active_scheduler.running:
        crawler_scheduler.shutdown_crawler_scheduler(active_scheduler)

    crawler_scheduler.settings.CRAWLER_SCHEDULER_ENABLED = original_enabled
    crawler_scheduler.settings.CRAWLER_INTERVAL_MINUTES = original_interval
    crawler_scheduler.SessionLocal = original_session_local
    crawler_scheduler.run_crawler = original_run_crawler
    crawler_scheduler._active_scheduler = original_active_scheduler
    crawler_scheduler.logger.removeHandler(handler)

print(json.dumps(results, indent=2))
assert all(results.values()), results
