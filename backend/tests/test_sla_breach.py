import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from main import app
from database.database import SessionLocal
from database.models import Document, Task
from services.sla_predictor import get_task_due_date, _task_breach_risk

client = TestClient(app)

def test_due_date_parsing():
    # Test absolute date formats
    t_abs = Task(deadline="2026-06-30", created_at=datetime(2026, 5, 1))
    due = get_task_due_date(t_abs)
    assert due == datetime(2026, 6, 30)

    # Test relative date formats (days)
    t_rel_days = Task(deadline="15 days", created_at=datetime(2026, 5, 1))
    due_days = get_task_due_date(t_rel_days)
    assert due_days == datetime(2026, 5, 16)

    # Test relative date formats (weeks)
    t_rel_weeks = Task(deadline="2 weeks", created_at=datetime(2026, 5, 1))
    due_weeks = get_task_due_date(t_rel_weeks)
    assert due_weeks == datetime(2026, 5, 15)

    # Test relative date formats (months)
    t_rel_months = Task(deadline="1 month", created_at=datetime(2026, 5, 1))
    due_months = get_task_due_date(t_rel_months)
    assert due_months == datetime(2026, 5, 31)


def test_overdue_and_probability():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Task created in the past, overdue
    t_overdue = Task(
        status="pending",
        deadline="10 days",
        created_at=now - timedelta(days=12),
        priority="High"
    )
    risk_overdue = _task_breach_risk(t_overdue)
    assert risk_overdue["is_overdue"] is True
    assert risk_overdue["breach_probability"] == 100
    assert risk_overdue["days_remaining"] < 0

    # Task completed in the past
    t_completed = Task(
        status="completed",
        deadline="10 days",
        created_at=now - timedelta(days=12),
        priority="High"
    )
    risk_completed = _task_breach_risk(t_completed)
    assert risk_completed["is_overdue"] is False
    assert risk_completed["breach_probability"] == 0

    # Task pending, near due
    t_near_due = Task(
        status="pending",
        deadline="10 days",
        created_at=now - timedelta(days=8),
        priority="Medium"
    )
    risk_near_due = _task_breach_risk(t_near_due)
    assert risk_near_due["is_overdue"] is False
    # Since 8 out of 10 days consumed, only 2 days left (80% time consumed).
    # Breach probability should be high but < 100.
    assert 60 <= risk_near_due["breach_probability"] < 100


def test_predictive_analytics_sla_metrics():
    db = SessionLocal()
    doc_id = "test-sla-doc"
    doc = Document(
        id=doc_id,
        filename="test_sla_doc.pdf",
        status="Indexed",
        regulator="RBI",
        framework="KYC"
    )
    db.add(doc)

    # 1. Overdue task (department A)
    t1 = Task(
        id="sla-t1",
        title="Action 1",
        department="Compliance",
        priority="High",
        status="pending",
        deadline="5 days",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7),
        document_id=doc_id
    )
    db.add(t1)

    # 2. On-track task (department A)
    t2 = Task(
        id="sla-t2",
        title="Action 2",
        department="Compliance",
        priority="Medium",
        status="pending",
        deadline="15 days",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=2),
        document_id=doc_id
    )
    db.add(t2)

    # 3. Completed task (department B)
    t3 = Task(
        id="sla-t3",
        title="Action 3",
        department="Operations",
        priority="High",
        status="completed",
        deadline="5 days",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=3),
        document_id=doc_id
    )
    db.add(t3)
    db.commit()

    try:
        response = client.get(f"/api/analytics?document_id={doc_id}")
        assert response.status_code == 200
        data = response.json()

        # Real metrics check
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 1
        assert data["completion_rate"] == 33.3
        assert data["overdue_tasks"] == 1
        assert data["tasks_at_risk_count"] == 0  # no pending tasks between 60% and 99%

        # Department performance check
        # Compliance has 2 tasks, 1 breached -> SLA Breach Rate = 50%
        # Operations has 1 task, 0 breached -> SLA Breach Rate = 0%
        performance = {item["department"]: item["sla_breach_rate"] for item in data["department_performance"]}
        assert performance["Compliance"] == 50.0
        assert performance["Operations"] == 0.0

    finally:
        db.query(Task).filter(Task.document_id == doc_id).delete()
        db.query(Document).filter(Document.id == doc_id).delete()
        db.commit()
        db.close()
