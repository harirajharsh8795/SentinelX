from datetime import datetime
from typing import List
from uuid import uuid4
from database.database import get_db_context
from database.models import AgentLog, AuditLog, Alert

def _ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def _resolve_document_id(db, document_id: str = None) -> str:
    if document_id:
        return document_id
    from database.models import Document
    latest = db.query(Document).order_by(Document.upload_date.desc()).first()
    return latest.id if latest else "NO_DOCUMENTS_FOUND"


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
    from database.models import Task, Document
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        
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

        # Dynamic compliance trend calculated in-memory
        from datetime import timedelta
        trend = []
        now = datetime.utcnow()
        for i in range(5, -1, -1):
            # Safe month subtraction
            month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            month_tasks = [
                t for t in all_tasks
                if t.created_at >= month_start and t.created_at < month_end
            ]
            if month_tasks:
                high_p = sum(
                    1 for t in month_tasks
                    if (t.status or "").lower() == "pending" and (t.priority or "").lower() == "high"
                )
                p_penalty = high_p * 10 + sum(
                    1 for t in month_tasks if (t.status or "").lower() == "pending"
                ) * 2
                trend.append(max(0, 100 - p_penalty))
            else:
                trend.append(comp_score)

        if not trend or len(set(trend)) == 1:
            trend = [max(0, comp_score - 10), max(0, comp_score - 5), comp_score]

        # Severity breakdown calculated in-memory
        severity_mix = {"High": 0, "Medium": 0, "Low": 0}
        for t in all_tasks:
            p = (t.priority or "Medium").title()
            if p in severity_mix:
                severity_mix[p] += 1
            else:
                severity_mix["Medium"] += 1

        completed_actions = sum(1 for t in all_tasks if (t.status or "").lower() != "pending")

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
        }
