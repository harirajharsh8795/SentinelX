from typing import Dict, Any, List
from datetime import datetime, timedelta
from database.database import SessionLocal
from database.models import Task, Document, Alert
from services.sla_predictor import compute_sla_predictions


def _build_monthly_trends(db, doc_id: str) -> tuple:
    if doc_id:
        tasks = db.query(Task).filter(Task.document_id == doc_id).all()
        alerts = db.query(Alert).filter(Alert.document_id == doc_id).all()
        docs = db.query(Document).filter(Document.id == doc_id).all()
    else:
        tasks = db.query(Task).all()
        alerts = db.query(Alert).all()
        docs = db.query(Document).all()
        
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str.split()[0], "%Y-%m-%d")
        except Exception:
            return None

    task_months = {(t.created_at.year, t.created_at.month) for t in tasks if t.created_at}
    alert_months = set()
    for a in alerts:
        if a.created_at:
            dt = parse_date(a.created_at)
            if dt:
                alert_months.add((dt.year, dt.month))
    doc_months = {(d.upload_date.year, d.upload_date.month) for d in docs if d.upload_date}
                
    all_months = task_months.union(alert_months).union(doc_months)
    historical_data_available = len(all_months) >= 2
    
    if not historical_data_available:
        return [], False
        
    min_year, min_month = min(all_months)
    max_year, max_month = max(all_months)
    
    curr_year, curr_month = min_year, min_month
    ordered_months = []
    while (curr_year, curr_month) <= (max_year, max_month):
        ordered_months.append((curr_year, curr_month))
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
            
    from collections import defaultdict
    monthly_data = defaultdict(lambda: {
        "risk_anomalies": 0,
        "resolved": 0,
        "risk_records": 0,
        "alerts": 0,
        "workflow_tasks": 0,
        "compliance_findings": 0
    })
    
    for d in docs:
        if not d.upload_date:
            continue
        y, m = d.upload_date.year, d.upload_date.month
        res = d.analysis_result
        if res and isinstance(res, dict):
            monthly_data[(y, m)]["compliance_findings"] += len(res.get("maps", []))
            monthly_data[(y, m)]["risk_records"] += len(res.get("risks", []))
            
    for t in tasks:
        if not t.created_at:
            continue
        y, m = t.created_at.year, t.created_at.month
        monthly_data[(y, m)]["workflow_tasks"] += 1
        if (t.priority or "").lower() == "high":
            monthly_data[(y, m)]["risk_anomalies"] += 1
        if (t.status or "").lower() == "completed":
            monthly_data[(y, m)]["resolved"] += 1
            
    for a in alerts:
        if not a.created_at:
            continue
        dt = parse_date(a.created_at)
        if dt:
            y, m = dt.year, dt.month
            monthly_data[(y, m)]["alerts"] += 1
            monthly_data[(y, m)]["risk_anomalies"] += 1
            
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    trend_list = []
    for y, m in ordered_months:
        label = f"{month_names[m]} '{str(y)[2:]}" if min_year != max_year else month_names[m]
        trend_list.append({
            "month": label,
            "risk_anomalies": monthly_data[(y, m)]["risk_anomalies"],
            "resolved": monthly_data[(y, m)]["resolved"],
            "risk_records": monthly_data[(y, m)]["risk_records"],
            "alerts": monthly_data[(y, m)]["alerts"],
            "workflow_tasks": monthly_data[(y, m)]["workflow_tasks"],
            "compliance_findings": monthly_data[(y, m)]["compliance_findings"]
        })
        
    return trend_list, True


def get_predictive_analytics(document_id: str = None) -> Dict[str, Any]:
    """
    Phase 6: Real predictive analytics from DB + SLA breach models.
    """
    from services.log_service import _resolve_document_id
    from services.task_service import ensure_tasks_and_alerts_synced
    from database.models import Alert
    
    db = SessionLocal()
    doc_id = _resolve_document_id(db, document_id)
    
    # Self-heal database records if missing but cached analysis exists
    ensure_tasks_and_alerts_synced(db, doc_id)
    
    tasks = db.query(Task).filter(Task.document_id == doc_id).all()
    alerts = db.query(Alert).filter(Alert.document_id == doc_id).all()
    sla = compute_sla_predictions(doc_id)

    from services.sla_predictor import _task_breach_risk
    
    overdue_count = 0
    at_risk_count = 0
    completed_count = 0
    
    overdue_tasks_list = []
    tasks_at_risk_list = []
    all_tasks_list = []
    
    dept_stats: Dict[str, Dict[str, int]] = {}
    for t in tasks:
        d = t.department or "General"
        if d not in dept_stats:
            dept_stats[d] = {"total": 0, "breached": 0, "at_risk": 0}
        dept_stats[d]["total"] += 1
        
        status_lower = (t.status or "").lower()
        if status_lower == "completed":
            completed_count += 1
            
        risk_info = _task_breach_risk(t)
        task_data = {
            "id": t.id,
            "title": t.title,
            "department": t.department or "General",
            "priority": t.priority or "Medium",
            "status": t.status or "pending",
            "deadline": t.deadline or "N/A",
            "due_date": risk_info.get("due_date") or "N/A",
            "days_remaining": risk_info.get("days_remaining"),
            "breach_probability": risk_info.get("breach_probability", 0),
            "is_overdue": risk_info.get("is_overdue", False)
        }
        all_tasks_list.append(task_data)
        
        if risk_info["is_overdue"]:
            overdue_count += 1
            dept_stats[d]["breached"] += 1
            overdue_tasks_list.append(task_data)
        elif risk_info["breach_probability"] >= 60:
            at_risk_count += 1
            dept_stats[d]["at_risk"] += 1
            tasks_at_risk_list.append(task_data)

    department_performance = []
    for dept, stats in dept_stats.items():
        rate = round((stats["breached"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
        department_performance.append({
            "department": dept,
            "sla_breach_rate": rate,
            "tasks_at_risk": stats["at_risk"],
        })

    if not department_performance:
        department_performance = [{"department": "No Data", "sla_breach_rate": 0, "tasks_at_risk": 0}]

    monthly_trends, hist_avail = _build_monthly_trends(db, doc_id)
    
    alerts_list = [
        {
            "id": a.id,
            "title": a.title,
            "severity": a.severity,
            "created_at": a.created_at
        }
        for a in alerts
    ]
    
    db.close()

    total_tasks_count = len(tasks)
    completion_rate = round((completed_count / total_tasks_count) * 100, 1) if total_tasks_count > 0 else 0

    return {
        "prediction_alert": sla["prediction_alert"],
        "anomaly_score": sla["anomaly_score"],
        "risk_propagation_index": sla["risk_propagation_index"],
        "sla_at_risk": sla["sla_at_risk"],
        "monthly_trends": monthly_trends,
        "department_performance": department_performance,
        "historical_data_available": hist_avail,
        "total_tasks": total_tasks_count,
        "completed_tasks": completed_count,
        "completion_rate": completion_rate,
        "overdue_tasks": overdue_count,
        "tasks_at_risk_count": at_risk_count,
        "overdue_tasks_list": overdue_tasks_list,
        "tasks_at_risk_list": tasks_at_risk_list,
        "all_tasks_list": all_tasks_list,
        "alerts_list": alerts_list
    }

