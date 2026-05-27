import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from utils.config import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def job_live_scrape_and_index():
    """Phase 8: Discover RBI/SEBI/CERT-IN circulars and auto-index PDFs."""
    if not settings.scrape_enabled:
        logger.info("Live scraping disabled (SCRAPING_ENABLED=false)")
        return
    logger.info("Cron: Starting live regulatory scrape + auto-index...")
    try:
        from services.live_ingestion_service import run_live_ingestion_sync
        result = run_live_ingestion_sync()
        logger.info(
            "Scrape complete: discovered=%s indexed=%s skipped=%s failed=%s",
            result.get("discovered", 0),
            result.get("indexed", 0),
            result.get("skipped", 0),
            result.get("failed", 0),
        )
    except Exception as exc:
        logger.error("Live ingestion cron failed: %s", exc)


def job_corpus_refresh():
    """Phase 7: Re-sync master corpus seed files (skips already ingested)."""
    logger.info("Cron: Refreshing master regulatory corpus...")
    try:
        from services.corpus_ingestion_service import ingest_all_corpus
        result = ingest_all_corpus(force=False)
        logger.info("Corpus refresh: %s new documents ingested", result.get("total_ingested", 0))
    except Exception as exc:
        logger.error("Corpus refresh failed: %s", exc)


def configure_scheduler() -> None:
    scheduler.add_job(
        job_live_scrape_and_index,
        CronTrigger(hour=0, minute=30),
        id="live_scrape",
        replace_existing=True,
    )
    scheduler.add_job(
        job_corpus_refresh,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="corpus_refresh",
        replace_existing=True,
    )
    if settings.scrape_interval_hours > 0 and settings.scrape_enabled:
        scheduler.add_job(
            job_live_scrape_and_index,
            IntervalTrigger(hours=settings.scrape_interval_hours),
            id="live_scrape_interval",
            replace_existing=True,
        )


def start_scheduler():
    configure_scheduler()
    if not scheduler.running:
        scheduler.start()
    logger.info("APScheduler started (live scrape + corpus refresh).")
