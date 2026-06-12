"""
Phase 8 — Live Web Scraping & Auto-Indexing Pipeline
Discovers RBI/SEBI/CERT-IN circulars, downloads PDFs, and indexes into ChromaDB.
"""
import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database.database import SessionLocal
from database.models import ScrapeRecord, Document
from scrapers import SCRAPERS
from scrapers.base_scraper import BaseScraper, ScrapedItem
from services.corpus_registry import get_source_by_code
from services.document_service import ingest_bytes
from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _is_already_scraped(url: str) -> bool:
    db = SessionLocal()
    exists = db.query(ScrapeRecord).filter(ScrapeRecord.source_url == url).first()
    db.close()
    return exists is not None


def _record_scrape(
    item: ScrapedItem,
    status: str,
    document_id: str = None,
    error: str = None,
) -> None:
    db = SessionLocal()
    existing = db.query(ScrapeRecord).filter(ScrapeRecord.source_url == item.url).first()
    if existing:
        existing.status = status
        existing.document_id = document_id
        existing.error_message = error
        existing.scraped_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        db.add(ScrapeRecord(
            regulator=item.regulator,
            title=item.title,
            source_url=item.url,
            document_id=document_id,
            status=status,
            error_message=error,
        ))
    db.commit()
    db.close()


async def ingest_scraped_item(item: ScrapedItem) -> Dict[str, Any]:
    """Download a single PDF and auto-index it."""
    if _is_already_scraped(item.url):
        return {"url": item.url, "status": "skipped", "reason": "already indexed"}

    scraper = SCRAPERS.get(item.regulator)
    if not scraper:
        raise ValueError(f"No scraper for {item.regulator}")

    content = scraper.download_bytes(item.url)
    if not content:
        _record_scrape(item, "failed", error="download failed or not a PDF")
        return {"url": item.url, "status": "failed", "reason": "download failed"}

    src = get_source_by_code(item.regulator)
    framework = src.framework if src else "Regulatory"
    filename = f"{item.regulator}_{BaseScraper.url_hash(item.url)}.pdf"
    external_id = f"scrape:{item.regulator}:{item.url}"

    try:
        result = await asyncio.to_thread(
            ingest_bytes,
            filename=filename,
            content=content,
            regulator=item.regulator,
            framework=framework,
            source_url=item.url,
            ingestion_type="scrape",
            external_id=external_id,
        )
        _record_scrape(item, "indexed", document_id=result["document_id"])
        return {"url": item.url, "status": "indexed", **result}
    except Exception as exc:
        _record_scrape(item, "failed", error=str(exc))
        return {"url": item.url, "status": "failed", "error": str(exc)}


async def run_live_ingestion(regulators: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Full Phase 8 pipeline: discover → download → auto-index for RBI, SEBI, CERT-IN.
    """
    if not settings.scrape_enabled:
        return {"status": "disabled", "message": "SCRAPING_ENABLED=false in config"}

    targets = regulators or ["RBI", "SEBI", "CERTIN"]
    results = {"discovered": 0, "indexed": 0, "skipped": 0, "failed": 0, "details": []}

    for reg in targets:
        scraper = SCRAPERS.get(reg.upper())
        if not scraper:
            continue
        try:
            items = scraper.discover()
        except Exception as exc:
            logger.error("Discovery failed for %s: %s", reg, exc)
            results["details"].append({"regulator": reg, "error": str(exc)})
            continue

        results["discovered"] += len(items)
        for item in items:
            outcome = await ingest_scraped_item(item)
            results["details"].append(outcome)
            st = outcome.get("status")
            if st == "indexed":
                results["indexed"] += 1
            elif st == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1

    return results


def run_live_ingestion_sync(regulators: Optional[List[str]] = None) -> Dict[str, Any]:
    """Synchronous wrapper for APScheduler cron jobs."""
    return asyncio.run(run_live_ingestion(regulators))


def get_scrape_status() -> Dict[str, Any]:
    db = SessionLocal()
    records = db.query(ScrapeRecord).order_by(ScrapeRecord.scraped_at.desc()).limit(50).all()
    stats = {
        "total": db.query(ScrapeRecord).count(),
        "indexed": db.query(ScrapeRecord).filter(ScrapeRecord.status == "indexed").count(),
        "failed": db.query(ScrapeRecord).filter(ScrapeRecord.status == "failed").count(),
        "pending": db.query(ScrapeRecord).filter(ScrapeRecord.status == "pending").count(),
    }
    db.close()
    return {
        "stats": stats,
        "recent": [
            {
                "regulator": r.regulator,
                "title": r.title,
                "url": r.source_url,
                "status": r.status,
                "document_id": r.document_id,
                "scraped_at": r.scraped_at.isoformat() if r.scraped_at else None,
            }
            for r in records
        ],
    }
