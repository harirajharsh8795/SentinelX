from typing import Dict, Any, List
from datetime import datetime, timedelta
from database.database import SessionLocal
from database.models import Task, Document, Alert
from services.sla_predictor import compute_sla_predictions


def _build_monthly_trends(db, doc_id: str) -> List[Dict[str, Any]]:
    """Phase 5/6: Build trend from real task and alert timestamps."""
    now = datetime.utcnow()
    trends = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        label = month_start.strftime("%b")

        tasks_in_month = db.query(Task).filter(
            Task.document_id == doc_id,
            Task.created_at >= month_start,
            Task.created_at < month_end,
        ).all()
        alerts_in_month = db.query(Alert).filter(Alert.document_id == doc_id).count() if i == 0 else 0

        pending = sum(1 for t in tasks_in_month if (t.status or "").lower() == "pending")
        resolved = len(tasks_in_month) - pending
        high_pending = sum(
            1 for t in tasks_in_month
            if (t.status or "").lower() == "pending" and (t.priority or "").lower() == "high"
        )

        trends.append({
            "month": label,
            "risk_anomalies": high_pending + alerts_in_month,
            "resolved": resolved,
        })

    if not any(t["risk_anomalies"] or t["resolved"] for t in trends):
        alert_count = db.query(Alert).filter(Alert.document_id == doc_id).count()
        task_count = db.query(Task).filter(Task.document_id == doc_id).count()
        current_month = now.strftime("%b")
        trends = [
            {"month": "Baseline", "risk_anomalies": 0, "resolved": 0},
            {
                "month": current_month,
                "risk_anomalies": alert_count,
                "resolved": max(0, task_count - db.query(Task).filter(Task.status == "pending", Task.document_id == doc_id).count()),
            },
        ]
    return trends


def get_predictive_analytics(document_id: str = None) -> Dict[str, Any]:
    """
    Phase 6: Real predictive analytics from DB + SLA breach models.
    """
    from services.log_service import _resolve_document_id
    db = SessionLocal()
    doc_id = _resolve_document_id(db, document_id)
    
    tasks = db.query(Task).filter(Task.document_id == doc_id).all()
    sla = compute_sla_predictions(doc_id)

    dept_stats: Dict[str, Dict[str, int]] = {}
    for t in tasks:
        d = t.department or "General"
        if d not in dept_stats:
            dept_stats[d] = {"total": 0, "breached": 0, "at_risk": 0}
        dept_stats[d]["total"] += 1

        from services.sla_predictor import _task_breach_risk
        breach_prob = _task_breach_risk(t)["breach_probability"]
        if breach_prob >= 60:
            dept_stats[d]["at_risk"] += 1
        if (t.status or "").lower() == "pending" and breach_prob >= 80:
            dept_stats[d]["breached"] += 1

    department_performance = []
    for dept, stats in dept_stats.items():
        rate = round((stats["at_risk"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        department_performance.append({
            "department": dept,
            "sla_breach_rate": rate,
            "tasks_at_risk": stats["at_risk"],
        })

    if not department_performance:
        department_performance = [{"department": "No Data", "sla_breach_rate": 0, "tasks_at_risk": 0}]

    monthly_trends = _build_monthly_trends(db, doc_id)
    db.close()

    return {
        "prediction_alert": sla["prediction_alert"],
        "anomaly_score": sla["anomaly_score"],
        "risk_propagation_index": sla["risk_propagation_index"],
        "sla_at_risk": sla["sla_at_risk"],
        "monthly_trends": monthly_trends,
        "department_performance": department_performance,
    }

