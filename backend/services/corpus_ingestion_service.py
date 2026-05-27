"""
Phase 7 — Master Regulatory Corpus Ingestion Pipeline
Bulk-ingests seed files and PDFs from data/corpus/ into ChromaDB + SQLite.
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from database.database import SessionLocal
from database.models import Document, RegulatorySource
from services.corpus_registry import REGULATORY_SOURCES, get_source_by_code
from services.document_service import ingest_file_from_path
from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _corpus_root() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corpus")


def seed_regulatory_sources() -> int:
    """Register all corpus sources in DB catalog."""
    db = SessionLocal()
    created = 0
    for src in REGULATORY_SOURCES:
        existing = db.query(RegulatorySource).filter(RegulatorySource.code == src.code).first()
        if existing:
            continue
        db.add(RegulatorySource(
            code=src.code,
            name=src.name,
            framework=src.framework,
            description=src.description,
            base_url=src.base_url,
            corpus_path=os.path.join(_corpus_root(), src.corpus_subdir),
            is_active=True,
        ))
        created += 1
    db.commit()
    db.close()
    return created


def _already_ingested(external_id: str) -> bool:
    db = SessionLocal()
    exists = db.query(Document).filter(Document.external_id == external_id).first()
    db.close()
    return exists is not None


def ingest_corpus_source(source_code: str, force: bool = False) -> Dict[str, Any]:
    """
    Ingest all .txt and .pdf files for a single regulator/framework.
    """
    src = get_source_by_code(source_code)
    if not src:
        raise ValueError(f"Unknown regulatory source: {source_code}")

    corpus_dir = os.path.join(_corpus_root(), src.corpus_subdir)
    if not os.path.isdir(corpus_dir):
        os.makedirs(corpus_dir, exist_ok=True)

    ingested = []
    skipped = []
    errors = []

    for filename in sorted(os.listdir(corpus_dir)):
        if not filename.lower().endswith((".txt", ".pdf")):
            continue
        filepath = os.path.join(corpus_dir, filename)
        external_id = f"corpus:{src.code}:{filename}"

        if not force and _already_ingested(external_id):
            skipped.append(filename)
            continue

        try:
            result = ingest_file_from_path(
                filepath=filepath,
                regulator=src.code,
                framework=src.framework,
                source_url=src.base_url,
                ingestion_type="corpus",
                external_id=external_id,
            )
            ingested.append(result)
        except Exception as exc:
            logger.error("Corpus ingest failed for %s: %s", filename, exc)
            errors.append({"file": filename, "error": str(exc)})

    _update_source_stats(src.code, len(ingested))
    return {
        "source": src.code,
        "ingested_count": len(ingested),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "ingested": ingested,
        "skipped": skipped,
        "errors": errors,
    }


def ingest_all_corpus(force: bool = False) -> Dict[str, Any]:
    """Bulk ingest entire master regulatory corpus."""
    seed_regulatory_sources()
    results = []
    total_ingested = 0
    for src in REGULATORY_SOURCES:
        r = ingest_corpus_source(src.code, force=force)
        results.append(r)
        total_ingested += r["ingested_count"]
    return {
        "total_sources": len(REGULATORY_SOURCES),
        "total_ingested": total_ingested,
        "sources": results,
    }


def _update_source_stats(code: str, new_docs: int) -> None:
    db = SessionLocal()
    src = db.query(RegulatorySource).filter(RegulatorySource.code == code).first()
    if src:
        src.document_count = (src.document_count or 0) + new_docs
        src.last_ingested_at = datetime.utcnow()
    db.commit()
    db.close()


def get_corpus_stats() -> Dict[str, Any]:
    db = SessionLocal()
    sources = db.query(RegulatorySource).all()
    by_regulator = {}
    for doc in db.query(Document).filter(Document.ingestion_type.in_(["corpus", "scrape"])).all():
        reg = doc.regulator or "Unknown"
        by_regulator[reg] = by_regulator.get(reg, 0) + 1
    db.close()

    return {
        "corpus_root": _corpus_root(),
        "registered_sources": len(sources) if sources else len(REGULATORY_SOURCES),
        "documents_by_regulator": by_regulator,
        "sources": [
            {
                "code": s.code,
                "name": s.name,
                "framework": s.framework,
                "document_count": s.document_count,
                "last_ingested_at": s.last_ingested_at.isoformat() if s.last_ingested_at else None,
                "base_url": s.base_url,
            }
            for s in sources
        ] if sources else [
            {"code": s.code, "name": s.name, "framework": s.framework}
            for s in REGULATORY_SOURCES
        ],
    }


def search_corpus(query: str, regulator: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search across corpus documents, optionally filtered by regulator."""
    from rag.hybrid_search import hybrid_search_and_rerank
    from database.database import SessionLocal
    from database.models import Document

    doc_ids = None
    if regulator:
        db = SessionLocal()
        docs = db.query(Document).filter(
            Document.regulator == regulator.upper(),
            Document.status == "Indexed",
        ).all()
        db.close()
        doc_ids = [d.id for d in docs] if docs else []
        if not doc_ids:
            return []

    return hybrid_search_and_rerank(query, final_k=top_k, doc_id=doc_ids, regulator=regulator)
