"""Phase 10-15: Graph, reports, observability, grounding tests."""
import pytest
from services.graph_service import _compute_risk_propagation, NODE_COLORS
from services.observability_service import (
    TraceContext,
    estimate_grounding_quality,
    get_metrics,
    record_hallucination_flag,
)
from services.report_service import generate_executive_pdf, generate_board_docx, generate_compliance_report_csv
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_risk_propagation_scores():
    nodes = [
        {"id": "r1", "type": "Risk", "severity": "High", "label": "KYC Risk"},
        {"id": "d1", "type": "Department", "label": "Compliance"},
    ]
    edges = [{"source": "r1", "target": "d1", "label": "threatens"}]
    result = _compute_risk_propagation(nodes, edges)
    risk = next(n for n in result if n["id"] == "r1")
    dept = next(n for n in result if n["id"] == "d1")
    assert risk["risk_score"] == 1.0
    assert dept["risk_score"] > 0


def test_grounding_quality_no_sources():
    q = estimate_grounding_quality("Some answer", [])
    assert q["risk"] == "high"


def test_trace_context_records():
    before = get_metrics()["total_requests"]
    with TraceContext("test.op"):
        pass
    after = get_metrics()["total_requests"]
    assert after == before + 1


def test_compliance_csv():
    csv = generate_compliance_report_csv()
    assert "COMPLIANCE SYSTEM REPORT" in csv


def test_executive_pdf_bytes():
    pdf = generate_executive_pdf()
    assert pdf[:4] == b"%PDF"


def test_board_docx_bytes():
    docx = generate_board_docx()
    assert docx[:2] == b"PK"


def test_observability_metrics_api():
    r = client.get("/api/observability/metrics")
    assert r.status_code == 200
    assert "total_requests" in r.json()


def test_observability_traces_api():
    r = client.get("/api/observability/traces?limit=5")
    assert r.status_code == 200
    assert "traces" in r.json()


def test_reports_pdf_endpoint():
    r = client.get("/api/reports/executive-pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


def test_reports_docx_endpoint():
    r = client.get("/api/reports/board-docx")
    assert r.status_code == 200
    assert "wordprocessingml" in r.headers["content-type"]
