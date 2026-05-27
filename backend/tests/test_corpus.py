"""Phase 7: Master Regulatory Corpus tests."""
import os
import pytest
from fastapi.testclient import TestClient

from main import app
from services.corpus_registry import REGULATORY_SOURCES, get_source_by_code
from services.corpus_ingestion_service import ingest_corpus_source, get_corpus_stats, seed_regulatory_sources

client = TestClient(app)


def test_registry_has_six_sources():
    assert len(REGULATORY_SOURCES) == 6
    codes = {s.code for s in REGULATORY_SOURCES}
    assert codes == {"RBI", "SEBI", "CERTIN", "NPCI", "SWIFT", "ISO27001"}


def test_get_source_by_code():
    rbi = get_source_by_code("RBI")
    assert rbi is not None
    assert "KYC" in rbi.framework or "Banking" in rbi.framework


def test_corpus_sources_api():
    response = client.get("/api/corpus/sources")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) == 6


def test_corpus_ingest_rbi():
    seed_regulatory_sources()
    result = ingest_corpus_source("RBI", force=False)
    assert result["source"] == "RBI"
    assert result["ingested_count"] >= 0


def test_corpus_stats():
    stats = get_corpus_stats()
    assert "registered_sources" in stats
    assert stats["corpus_root"]
