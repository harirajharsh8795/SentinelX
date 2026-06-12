import sys
sys.path.append("e:/Desktop/CANARA SENTINEL AI/backend")
from database.database import get_db_context
from database.models import Document, Task, Alert

with get_db_context() as db:
    docs = db.query(Document).all()
    print("=== Documents ===")
    for d in docs:
        tasks_count = db.query(Task).filter(Task.document_id == d.id).count()
        alerts_count = db.query(Alert).filter(Alert.document_id == d.id).count()
        print(f"Doc ID: {d.id} | Filename: {d.filename} | Tasks: {tasks_count} | Alerts: {alerts_count} | HasResult: {d.analysis_result is not None}")
