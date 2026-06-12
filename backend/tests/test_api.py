import pytest
from fastapi.testclient import TestClient
from main import app

# Phase 14: System Testing & CI/CD
client = TestClient(app)

def test_health_check():
    """Test if the FastApi root endpoint is healthy."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_dashboard_api(test_document):
    """Test the dashboard integration."""
    response = client.get(f"/api/dashboard?document_id={test_document}")
    assert response.status_code == 200
    data = response.json()
    assert "compliance_score" in data

def test_compliance_report(test_document):
    """Test the CSV generation."""
    response = client.get(f"/api/reports/compliance?document_id={test_document}")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    # Minimal check for CSV content
    assert b"COMPLIANCE SYSTEM REPORT" in response.content
