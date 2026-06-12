"""
Phase 6 — Real Predictive Analytics
Date-based SLA breach prediction and risk propagation heuristics.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from database.database import SessionLocal
from database.models import Task, Alert, Document


def get_task_due_date(task) -> Optional[datetime]:
    if not task.deadline:
        return None
    deadline_clean = task.deadline.strip()
    # Try parsing as absolute date first
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(deadline_clean, fmt)
        except ValueError:
            continue
            
    # Try relative parsing
    m = re.search(r"(\d+)\s*(day|days|month|months|week|weeks)", deadline_clean.lower())
    if m:
        n, unit = int(m.group(1)), m.group(2)
        created = task.created_at or datetime.now(timezone.utc).replace(tzinfo=None)
        if "month" in unit:
            return created + timedelta(days=n * 30)
        elif "week" in unit:
            return created + timedelta(days=n * 7)
        else:
            return created + timedelta(days=n)
    return None


def _task_breach_risk(task) -> Dict[str, Any]:
    """Score SLA breach probability 0-100 based on due date proximity and actual overdue status."""
    due_date = get_task_due_date(task)
    if not due_date:
        return {
            "task_id": task.id,
            "title": task.title,
            "department": task.department,
            "breach_probability": 0,
            "is_overdue": False,
            "days_remaining": None,
            "due_date": None,
        }
        
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if task.status and task.status.lower() == "completed":
        return {
            "task_id": task.id,
            "title": task.title,
            "department": task.department,
            "breach_probability": 0,
            "is_overdue": False,
            "days_remaining": (due_date - now).days,
            "due_date": due_date.strftime("%Y-%m-%d"),
        }
        
    is_overdue = now > due_date
    if is_overdue:
        prob = 100
    else:
        created = task.created_at or now
        total_seconds = (due_date - created).total_seconds()
        time_left = (due_date - now).total_seconds()
        ratio_left = max(0.0, time_left / total_seconds) if total_seconds > 0 else 0.0
        
        # Priority multiplier
        priority = (task.priority or "").lower()
        multiplier = 1.0
        if priority == "high":
            multiplier = 1.5
        elif priority == "medium":
            multiplier = 1.2
            
        prob = min(99, round((1.0 - ratio_left) * 100 * multiplier))
        
    return {
        "task_id": task.id,
        "title": task.title,
        "department": task.department,
        "breach_probability": prob,
        "is_overdue": is_overdue,
        "days_remaining": (due_date - now).days,
        "due_date": due_date.strftime("%Y-%m-%d"),
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
