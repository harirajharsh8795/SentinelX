import pytest
from main import app
from api.auth import get_current_active_user
from models.auth_schemas import User

@pytest.fixture(autouse=True)
def override_auth():
    dummy_user = User(
        username="test_user",
        role="Admin",
        is_active=True
    )
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def test_document():
    from datetime import datetime, timezone
    from database.database import SessionLocal
    from database.models import Document, Task, Alert
    db = SessionLocal()
    
    # Check if a test document already exists
    doc = db.query(Document).filter(Document.id == "test-doc-id").first()
    if not doc:
        doc = Document(
            id="test-doc-id",
            filename="test_document.pdf",
            status="Indexed",
            regulator="RBI",
            framework="KYC"
        )
        db.add(doc)
        
        # Add a task and alert for this document to make reports work
        task = Task(
            id="test-task-id",
            title="Update KYC policy",
            department="Compliance",
            priority="High",
            status="pending",
            deadline="30 days",
            document_id="test-doc-id"
        )
        db.add(task)
        
        alert = Alert(
            id="test-alert-id",
            title="KYC breach risk alert",
            severity="High",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S UTC"),
            document_id="test-doc-id"
        )
        db.add(alert)
        
        db.commit()
    
    yield "test-doc-id"
    
    # Clean up
    db = SessionLocal()
    db.query(Task).filter(Task.document_id == "test-doc-id").delete()
    db.query(Alert).filter(Alert.document_id == "test-doc-id").delete()
    db.query(Document).filter(Document.id == "test-doc-id").delete()
    db.commit()
    db.close()

