from datetime import datetime, timezone
from typing import List
from uuid import uuid4
from database.database import get_db_context
from database.models import AgentLog, AuditLog, Alert

def _ts() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S UTC")


def _resolve_document_id(db, document_id: str = None) -> str:
    if document_id and document_id.strip() and document_id.lower().strip() not in ("null", "undefined", ""):
        return document_id
    from database.models import Document
    latest = db.query(Document).order_by(Document.upload_date.desc()).first()
    if latest:
        return latest.id
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="Active document_id is required and database is empty.")



def add_agent_logs(agents: List[str], document_id: str = None) -> None:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        for agent in agents:
            log = AgentLog(
                id=str(uuid4()),
                agent=agent,
                action="Executed analysis pipeline",
                timestamp=_ts(),
                document_id=doc_id
            )
            db.add(log)
        db.commit()


def add_audit_events(events: List[str], document_id: str = None) -> None:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        for event in events:
            log = AuditLog(
                id=str(uuid4()),
                event=event,
                timestamp=_ts(),
                document_id=doc_id
            )
            db.add(log)
        db.commit()


def add_alerts(alerts: List[str], document_id: str = None) -> None:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        for alert in alerts:
            a = Alert(
                id=str(uuid4()),
                title=alert,
                severity="High" if any(w in alert.lower() for w in ["critical", "immediate", "penalty", "high", "severe"]) else "Medium",
                created_at=_ts(),
                document_id=doc_id
            )
            db.add(a)
        db.commit()


def get_agent_logs(document_id: str = None) -> List[dict]:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        logs = db.query(AgentLog).filter(AgentLog.document_id == doc_id).order_by(AgentLog.timestamp.desc()).limit(20).all()
        return [{"id": l.id, "agent": l.agent, "action": l.action, "timestamp": l.timestamp} for l in logs]


def get_audit_trail(document_id: str = None) -> List[dict]:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        logs = db.query(AuditLog).filter(AuditLog.document_id == doc_id).order_by(AuditLog.timestamp.desc()).limit(50).all()
        return [{"id": l.id, "event": l.event, "timestamp": l.timestamp} for l in logs]


def get_alerts(document_id: str = None) -> List[dict]:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        alerts = db.query(Alert).filter(Alert.document_id == doc_id).order_by(Alert.created_at.desc()).limit(20).all()
        return [{"id": a.id, "title": a.title, "severity": a.severity, "created_at": a.created_at} for a in alerts]


def get_dashboard(document_id: str = None) -> dict:
    from database.models import Task, Document, Alert
    from services.task_service import ensure_tasks_and_alerts_synced
    
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        
        # Self-heal missing database records from cached analysis
        ensure_tasks_and_alerts_synced(db, doc_id)
        
        alert_count = db.query(Alert).filter(Alert.document_id == doc_id).count()
        total_docs = db.query(Document).count()
        
        # Load all tasks once to optimize DB queries
        all_tasks = db.query(Task).filter(Task.document_id == doc_id).all()
        total_tasks = len(all_tasks)
        pending_tasks = sum(1 for t in all_tasks if (t.status or "").lower() == "pending")
        high_priority_pending = sum(
            1 for t in all_tasks
            if (t.status or "").lower() == "pending" and (t.priority or "").lower() == "high"
        )
        
        if total_tasks == 0:
            comp_score = 100
        else:
            penalty = (high_priority_pending * 10) + ((pending_tasks - high_priority_pending) * 2)
            comp_score = max(0, 100 - penalty)
            
        recent_docs = db.query(Document).order_by(Document.upload_date.desc()).limit(3).all()
        recent_doc_names = [d.filename for d in recent_docs]

        # Genuine compliance trend calculated from document-derived tasks, alerts, and documents
        task_months = {(t.created_at.year, t.created_at.month) for t in all_tasks if t.created_at}
        alerts = db.query(Alert).filter(Alert.document_id == doc_id).all()
        alert_months = set()
        for a in alerts:
            if a.created_at:
                try:
                    dt = datetime.strptime(a.created_at.split()[0], "%Y-%m-%d")
                    alert_months.add((dt.year, dt.month))
                except Exception:
                    pass
        
        doc_record = db.query(Document).filter(Document.id == doc_id).first()
        doc_months = set()
        if doc_record and doc_record.upload_date:
            doc_months.add((doc_record.upload_date.year, doc_record.upload_date.month))
            
        all_months = task_months.union(alert_months).union(doc_months)
        historical_data_available = len(all_months) >= 2
        
        trend = []
        if historical_data_available:
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
            
            for y, m in ordered_months:
                if m == 12:
                    month_end = datetime(y + 1, 1, 1)
                else:
                    month_end = datetime(y, m + 1, 1)
                
                historical_tasks = [t for t in all_tasks if t.created_at and t.created_at < month_end]
                hist_pending = sum(1 for t in historical_tasks if (t.status or "").lower() == "pending")
                hist_high_pending = sum(
                    1 for t in historical_tasks
                    if (t.status or "").lower() == "pending" and (t.priority or "").lower() == "high"
                )
                
                if not historical_tasks:
                    c_score = 100
                else:
                    p_penalty = (hist_high_pending * 10) + ((hist_pending - hist_high_pending) * 2)
                    c_score = max(0, 100 - p_penalty)
                trend.append(c_score)
        else:
            trend = []

        # Severity breakdown calculated in-memory
        severity_mix = {"High": 0, "Medium": 0, "Low": 0}
        for t in all_tasks:
            p = (t.priority or "Medium").title()
            if p in severity_mix:
                severity_mix[p] += 1
            else:
                severity_mix["Medium"] += 1

        completed_actions = sum(1 for t in all_tasks if (t.status or "").lower() != "pending")

        # Dynamic Exposure Index from alerts in DB
        high_alerts = sum(1 for a in alerts if (a.severity or "").lower() == "high")
        medium_alerts = sum(1 for a in alerts if (a.severity or "").lower() == "medium")
        low_alerts = len(alerts) - high_alerts - medium_alerts
        exposure_index = min(100, high_alerts * 15 + medium_alerts * 10 + low_alerts * 5)
        
        exposure_index_details = {
            "high_count": high_alerts,
            "medium_count": medium_alerts,
            "low_count": low_alerts,
            "score": exposure_index,
            "formula": "min(100, High Alerts * 15 + Medium Alerts * 10 + Low Alerts * 5)",
            "explanation": f"Exposure Index details: {high_alerts} High (15 pts), {medium_alerts} Medium (10 pts), {low_alerts} Low (5 pts)."
        }
        
        compliance_score_details = {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "high_priority_pending": high_priority_pending,
            "score": comp_score,
            "formula": "max(0, 100 - (High Pending Tasks * 10 + Other Pending Tasks * 2))",
            "explanation": f"Compliance Score details: Starts at 100%, subtracts 10% for each of the {high_priority_pending} High priority pending tasks, and 2% for each of the {pending_tasks - high_priority_pending} other pending tasks."
        }

        # Query all documents for Indexed Documents drilldown
        all_docs = db.query(Document).order_by(Document.upload_date.desc()).all()
        documents_list = [
            {
                "id": d.id,
                "filename": d.filename,
                "upload_date": d.upload_date.isoformat() if d.upload_date else "",
                "status": d.status,
                "regulator": d.regulator,
                "framework": d.framework
            }
            for d in all_docs
        ]

        tasks_list = [
            {
                "id": t.id,
                "title": t.title,
                "department": t.department,
                "priority": t.priority,
                "status": t.status,
                "deadline": t.deadline
            }
            for t in all_tasks
        ]

        alerts_list = [
            {
                "id": a.id,
                "title": a.title,
                "severity": a.severity,
                "created_at": a.created_at
            }
            for a in alerts
        ]

        return {
            "compliance_score": comp_score,
            "total_documents": total_docs,
            "pending_actions": pending_tasks,
            "risk_alerts": alert_count,
            "recent_uploads": recent_doc_names,
            "trend": trend,
            "severity_mix": severity_mix,
            "open_actions": pending_tasks,
            "completed_actions": completed_actions,
            "historical_data_available": historical_data_available,
            "tasks_list": tasks_list,
            "alerts_list": alerts_list,
            "documents_list": documents_list,
            "exposure_index": exposure_index,
            "exposure_index_details": exposure_index_details,
            "compliance_score_details": compliance_score_details
        }
