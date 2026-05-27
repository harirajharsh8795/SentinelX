"""
Phase 6 — Real Predictive Analytics
Date-based SLA breach prediction and risk propagation heuristics.
"""
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database.database import SessionLocal
from database.models import Task, Alert, Document


def _parse_deadline_days(deadline: str) -> Optional[int]:
    if not deadline:
        return None
    m = re.search(r"(\d+)\s*(day|days|month|months|week|weeks)", deadline.lower())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if "month" in unit:
        return n * 30
    if "week" in unit:
        return n * 7
    return n


def _task_breach_risk(task) -> Dict[str, Any]:
    """Score SLA breach probability 0-100 based on age, priority, and deadline proximity."""
    days_left = _parse_deadline_days(task.deadline or "")
    age_days = (datetime.utcnow() - (task.created_at or datetime.utcnow())).days

    score = 10.0
    priority = (task.priority or "").lower()
    if priority == "high":
        score += 25
    elif priority == "medium":
        score += 12

    if task.status and task.status.lower() == "pending":
        score += 15

    if days_left is not None:
        if days_left <= 7:
            score += 35
        elif days_left <= 14:
            score += 20
        elif days_left <= 30:
            score += 10
        if age_days > days_left * 0.7:
            score += 20  # consumed most of SLA window

    return {
        "task_id": task.id,
        "title": task.title,
        "department": task.department,
        "breach_probability": min(100, round(score)),
        "days_remaining": days_left,
    }


def compute_sla_predictions(document_id: str = None) -> Dict[str, Any]:
    from services.log_service import _resolve_document_id
    db = SessionLocal()
    doc_id = _resolve_document_id(db, document_id)
    
    tasks = db.query(Task).filter(Task.status == "pending", Task.document_id == doc_id).all()
    alerts = db.query(Alert).filter(Alert.document_id == doc_id).all()
    docs = db.query(Document).count()
    db.close()


    predictions = [_task_breach_risk(t) for t in tasks]
    high_risk = [p for p in predictions if p["breach_probability"] >= 60]

    # Anomaly score: ratio of high-severity pending work
    total_pending = len(predictions)
    anomaly_score = 0
    if total_pending:
        anomaly_score = round((len(high_risk) / total_pending) * 100)

    # Risk propagation: unresolved high-priority tasks amplify alert severity
    propagation_factor = min(100, len(high_risk) * 12 + len(alerts) * 5)

    forecast_msg = "All compliance systems are nominal."
    if len(high_risk) >= 3:
        high_risk_depts = list({p['department'] for p in high_risk if p.get('department')})
        dept_str = f" in {', '.join(high_risk_depts[:2])}" if high_risk_depts else ""
        forecast_msg = (
            f"Critical: {len(high_risk)} tasks have >60% SLA breach probability. "
            f"Based on unresolved MAPs{dept_str}, cyber compliance exposure may increase by {propagation_factor}% within 14 days."
        )
    elif len(high_risk) > 0:
        high_risk_depts = list({p['department'] for p in high_risk if p.get('department')})
        dept_str = f" in {', '.join(high_risk_depts[:2])}" if high_risk_depts else ""
        forecast_msg = (
            f"Warning: {len(high_risk)} pending task(s) approaching SLA breach{dept_str}. "
            f"Compliance exposure is projected to escalate to {propagation_factor}%."
        )
    elif len(alerts) > 0:
        forecast_msg = f"Attention: {len(alerts)} active alerts detected. Compliance exposure is at {propagation_factor}%."

    return {
        "prediction_alert": forecast_msg,
        "anomaly_score": anomaly_score,
        "risk_propagation_index": propagation_factor,
        "sla_at_risk": high_risk[:10],
        "total_documents": docs,
        "pending_tasks": total_pending,
    }
