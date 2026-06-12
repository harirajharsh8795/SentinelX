import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from database.database import SessionLocal
from database.models import Document, Task, Alert

client = TestClient(app)

def test_insufficient_historical_data(test_document):
    # Retrieve dashboard API response for the default test document (which has 1 task/1 alert in same month)
    response = client.get(f"/api/dashboard?document_id={test_document}")
    assert response.status_code == 200
    data = response.json()
    assert data["historical_data_available"] is False
    assert data["trend"] == []

    # Retrieve analytics API response
    response_an = client.get(f"/api/analytics?document_id={test_document}")
    assert response_an.status_code == 200
    data_an = response_an.json()
    assert data_an["historical_data_available"] is False
    assert data_an["monthly_trends"] == []


def test_sufficient_historical_data():
    db = SessionLocal()
    # Create temporary doc
    doc_id = "test-hist-doc-id"
    doc = Document(
        id=doc_id,
        filename="test_hist.pdf",
        status="Indexed",
        regulator="RBI",
        framework="KYC",
        upload_date=datetime(2026, 5, 20)
    )
    db.add(doc)
    
    # Task in month 1
    t1 = Task(
        id="task-m1",
        title="Task Month 1",
        department="Compliance",
        priority="High",
        status="pending",
        deadline="30 days",
        document_id=doc_id,
        created_at=datetime(2026, 4, 15, 12, 0, 0)
    )
    db.add(t1)
    
    # Task in month 2
    t2 = Task(
        id="task-m2",
        title="Task Month 2",
        department="Compliance",
        priority="Medium",
        status="completed",
        deadline="30 days",
        document_id=doc_id,
        created_at=datetime(2026, 5, 20, 12, 0, 0)
    )
    db.add(t2)
    db.commit()

    try:
        # Fetch dashboard API response
        response = client.get(f"/api/dashboard?document_id={doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["historical_data_available"] is True
        assert len(data["trend"]) == 2  # April & May
        assert data["trend"][0] == 90  # April: 1 pending high task (penalty 10) -> score 90
        # May: 1 pending high (April) + 1 completed (May) -> 1 pending high task -> score 90
        assert data["trend"][1] == 90

        # Fetch analytics API response
        response_an = client.get(f"/api/analytics?document_id={doc_id}")
        assert response_an.status_code == 200
        data_an = response_an.json()
        assert data_an["historical_data_available"] is True
        assert len(data_an["monthly_trends"]) == 2
        
        # April
        assert data_an["monthly_trends"][0]["month"] == "Apr"
        assert data_an["monthly_trends"][0]["risk_anomalies"] == 1
        assert data_an["monthly_trends"][0]["resolved"] == 0
        assert "risk_records" in data_an["monthly_trends"][0]
        assert "alerts" in data_an["monthly_trends"][0]
        assert data_an["monthly_trends"][0]["workflow_tasks"] == 1
        assert "compliance_findings" in data_an["monthly_trends"][0]
        
        # May
        assert data_an["monthly_trends"][1]["month"] == "May"
        assert data_an["monthly_trends"][1]["risk_anomalies"] == 0
        assert data_an["monthly_trends"][1]["resolved"] == 1
        assert data_an["monthly_trends"][1]["workflow_tasks"] == 1

    finally:
        # Cleanup
        db.query(Task).filter(Task.document_id == doc_id).delete()
        db.query(Alert).filter(Alert.document_id == doc_id).delete()
        db.query(Document).filter(Document.id == doc_id).delete()
        db.commit()
        db.close()
