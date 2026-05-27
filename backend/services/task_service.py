from typing import List
from uuid import uuid4
from database.database import get_db_context
from database.models import Task

def _resolve_document_id(db, document_id: str = None) -> str:
    if document_id:
        return document_id
    from database.models import Document
    latest = db.query(Document).order_by(Document.upload_date.desc()).first()
    return latest.id if latest else "NO_DOCUMENTS_FOUND"


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

