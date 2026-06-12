from typing import List
from uuid import uuid4
from database.database import get_db_context
from database.models import Task

def _resolve_document_id(db, document_id: str = None) -> str:
    if document_id and document_id.strip() and document_id.lower().strip() not in ("null", "undefined", ""):
        return document_id
    from database.models import Document
    latest = db.query(Document).order_by(Document.upload_date.desc()).first()
    if latest:
        return latest.id
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail="Active document_id is required and database is empty.")



def set_tasks_from_maps(maps: List[dict], document_id: str = None) -> None:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        
        existing_tasks = db.query(Task).filter(Task.document_id == doc_id).all()
        existing_titles = [t.title for t in existing_tasks]
        
        from rapidfuzz import fuzz
        
        for item in maps:
            title = item["title"]
            is_duplicate = False
            for ext_title in existing_titles:
                ratio = fuzz.token_sort_ratio(title.lower().strip(), ext_title.lower().strip())
                if ratio > 90.0:
                    is_duplicate = True
                    break
                    
            if not is_duplicate:
                task = Task(
                    id=str(uuid4()),
                    title=title,
                    department=item["department"],
                    priority=item["severity"],
                    status="pending",
                    deadline=item["deadline"],
                    document_id=doc_id
                )
                db.add(task)
                existing_titles.append(title)
                
        db.commit()


def get_tasks(document_id: str = None) -> List[dict]:
    with get_db_context() as db:
        doc_id = _resolve_document_id(db, document_id)
        tasks = db.query(Task).filter(Task.document_id == doc_id).all()
        return [
            {
                "id": t.id,
                "title": t.title,
                "department": t.department,
                "priority": t.priority,
                "status": t.status,
                "deadline": t.deadline
            }
            for t in tasks
        ]


def ensure_tasks_and_alerts_synced(db, doc_id: str) -> None:
    from database.models import Document, Task, Alert
    from datetime import datetime, timezone
    from uuid import uuid4
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or not doc.analysis_result:
        return
        
    res_dict = dict(doc.analysis_result)
    maps = res_dict.get("maps", [])
    risks = res_dict.get("risks", [])
    
    tasks_count = db.query(Task).filter(Task.document_id == doc_id).count()
    if tasks_count == 0 and maps:
        from services.task_service import set_tasks_from_maps
        set_tasks_from_maps(maps, doc_id)
        
    alerts_count = db.query(Alert).filter(Alert.document_id == doc_id).count()
    if alerts_count == 0 and risks:
        alerts_to_sync = res_dict.get("alerts", [])
        if not alerts_to_sync:
            alerts_to_sync = [
                f"Vulnerability risk alert: {r.get('risk')}" 
                for r in risks
                if str(r.get("severity", "Medium")).lower() == "high"
            ]
            if not alerts_to_sync:
                alerts_to_sync = [
                    f"Vulnerability risk alert: {r.get('risk')}" 
                    for r in risks
                ]
            res_dict["alerts"] = alerts_to_sync
            doc.analysis_result = res_dict
            db.commit()
            
        existing_alerts = db.query(Alert).filter(Alert.document_id == doc_id).all()
        existing_titles = {a.title for a in existing_alerts}
        alerts_to_add = [alt for alt in alerts_to_sync if alt not in existing_titles]
        if alerts_to_add:
            for alert in alerts_to_add:
                a = Alert(
                    id=str(uuid4()),
                    title=alert,
                    severity="High" if any(w in alert.lower() for w in ["critical", "immediate", "penalty", "high", "severe"]) else "Medium",
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    document_id=doc_id
                )
                db.add(a)
            db.commit()


