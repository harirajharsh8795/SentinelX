import pytest
from fastapi.testclient import TestClient
from main import app
from database.database import SessionLocal
from database.models import Document, Task, Alert, AgentLog, AuditLog

client = TestClient(app)

@pytest.fixture(scope="module")
def seeded_isolation_documents():
    db = SessionLocal()
    
    # 1. Create RBI Document and child records
    rbi_doc = Document(
        id="iso-rbi-doc",
        filename="rbi_isolation_circular.pdf",
        status="Indexed",
        regulator="RBI",
        framework="KYC"
    )
    db.add(rbi_doc)
    
    rbi_task = Task(
        id="iso-rbi-task",
        title="RBI specific task",
        department="Compliance",
        priority="High",
        status="pending",
        deadline="30 days",
        document_id="iso-rbi-doc"
    )
    db.add(rbi_task)
    
    rbi_alert = Alert(
        id="iso-rbi-alert",
        title="RBI KYC alert",
        severity="High",
        created_at="2026-05-31 12:00:00 UTC",
        document_id="iso-rbi-doc"
    )
    db.add(rbi_alert)
    
    rbi_log = AgentLog(
        id="iso-rbi-log",
        agent="Compliance Agent",
        action="RBI compliance check",
        timestamp="2026-05-31 12:00:00 UTC",
        document_id="iso-rbi-doc"
    )
    db.add(rbi_log)
    
    rbi_audit = AuditLog(
        id="iso-rbi-audit",
        event="RBI Audit log entry",
        timestamp="2026-05-31 12:00:00 UTC",
        document_id="iso-rbi-doc"
    )
    db.add(rbi_audit)
    
    # 2. Create SEBI Document and child records
    sebi_doc = Document(
        id="iso-sebi-doc",
        filename="sebi_isolation_circular.pdf",
        status="Indexed",
        regulator="SEBI",
        framework="Mutual Funds"
    )
    db.add(sebi_doc)
    
    sebi_task = Task(
        id="iso-sebi-task",
        title="SEBI specific task",
        department="Investments",
        priority="High",
        status="pending",
        deadline="30 days",
        document_id="iso-sebi-doc"
    )
    db.add(sebi_task)
    
    sebi_alert = Alert(
        id="iso-sebi-alert",
        title="SEBI KYC alert",
        severity="High",
        created_at="2026-05-31 12:00:00 UTC",
        document_id="iso-sebi-doc"
    )
    db.add(sebi_alert)
    
    sebi_log = AgentLog(
        id="iso-sebi-log",
        agent="Compliance Agent",
        action="SEBI compliance check",
        timestamp="2026-05-31 12:00:00 UTC",
        document_id="iso-sebi-doc"
    )
    db.add(sebi_log)
    
    sebi_audit = AuditLog(
        id="iso-sebi-audit",
        event="SEBI Audit log entry",
        timestamp="2026-05-31 12:00:00 UTC",
        document_id="iso-sebi-doc"
    )
    db.add(sebi_audit)
    
    db.commit()
    db.close()
    
    yield
    
    # Clean up
    db = SessionLocal()
    for doc_id in ["iso-rbi-doc", "iso-sebi-doc"]:
        db.query(Task).filter(Task.document_id == doc_id).delete()
        db.query(Alert).filter(Alert.document_id == doc_id).delete()
        db.query(AgentLog).filter(AgentLog.document_id == doc_id).delete()
        db.query(AuditLog).filter(AuditLog.document_id == doc_id).delete()
        db.query(Document).filter(Document.id == doc_id).delete()
    db.commit()
    db.close()

def test_missing_document_id_returns_400(seeded_isolation_documents):
    """Calling endpoints without a document_id parameter should fall back to latest doc and return 200."""
    endpoints = [
        "/api/dashboard",
        "/api/tasks",
        "/api/alerts",
        "/api/agent-logs",
        "/api/audit-trail",
        "/api/reports/compliance",
        "/api/reports/executive-pdf",
        "/api/reports/board-docx",
        "/api/analytics",
    ]
    for ep in endpoints:
        response = client.get(ep)
        assert response.status_code == 200, f"Endpoint {ep} did not return 200 when falling back to latest doc."


def test_rbi_document_isolation(seeded_isolation_documents):
    """RBI document endpoints return RBI data and strictly no SEBI data/references."""
    # Dashboard API
    resp = client.get("/api/dashboard?document_id=iso-rbi-doc")
    assert resp.status_code == 200
    data = resp.json()
    assert "compliance_score" in data
    
    # Tasks API
    resp = client.get("/api/tasks?document_id=iso-rbi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "RBI specific task"
    assert items[0]["department"] == "Compliance"
    
    # Alerts API
    resp = client.get("/api/alerts?document_id=iso-rbi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "RBI KYC alert"
    
    # Agent Logs API
    resp = client.get("/api/agent-logs?document_id=iso-rbi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["action"] == "RBI compliance check"
    
    # Audit Trail API
    resp = client.get("/api/audit-trail?document_id=iso-rbi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["event"] == "RBI Audit log entry"

def test_sebi_document_isolation(seeded_isolation_documents):
    """SEBI document endpoints return SEBI data and strictly no RBI data/references."""
    # Tasks API
    resp = client.get("/api/tasks?document_id=iso-sebi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "SEBI specific task"
    assert items[0]["department"] == "Investments"
    
    # Alerts API
    resp = client.get("/api/alerts?document_id=iso-sebi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "SEBI KYC alert"
    
    # Agent Logs API
    resp = client.get("/api/agent-logs?document_id=iso-sebi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["action"] == "SEBI compliance check"
    
    # Audit Trail API
    resp = client.get("/api/audit-trail?document_id=iso-sebi-doc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["event"] == "SEBI Audit log entry"
