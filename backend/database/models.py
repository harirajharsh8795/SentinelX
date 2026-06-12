from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from uuid import uuid4
from .database import Base

def generate_uuid():
    return str(uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="Officer") # Admin, Auditor, Officer
    is_active = Column(Boolean, default=True)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    filename = Column(String, index=True)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    status = Column(String, default="Indexed") # Pending, Processing, Indexed, Failed
    uploader_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String)
    storage_uri = Column(String, nullable=True) # Phase 6
    pages = Column(Integer, default=0)

    # Phase 7: Master Regulatory Corpus metadata
    regulator = Column(String, nullable=True, index=True)   # RBI, SEBI, CERT-IN, NPCI, SWIFT, ISO
    framework = Column(String, nullable=True)               # KYC, AML, Cyber, PCI-DSS, etc.
    source_url = Column(String, nullable=True)
    ingestion_type = Column(String, default="upload")       # upload | corpus | scrape
    external_id = Column(String, nullable=True, index=True)  # dedupe key for scraped URLs

    # Phase 9: Document Versioning & Temporal Analysis
    version = Column(Integer, default=1)
    circular_id = Column(String, nullable=True)     # Common ID for linking versions (e.g. RBI/2026/01)
    effective_date = Column(DateTime, nullable=True)
    
    # Caching structured analysis output to avoid redundant API queries
    analysis_result = Column(JSON, nullable=True)
    knowledge_graph = Column(JSON, nullable=True)

    uploader = relationship("User")
    tasks = relationship("Task", back_populates="document")


class RegulatorySource(Base):
    """Phase 7: Catalog of supported regulatory frameworks."""
    __tablename__ = "regulatory_sources"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    code = Column(String, unique=True, index=True)          # RBI, SEBI, CERTIN, NPCI, SWIFT, ISO27001
    name = Column(String)
    framework = Column(String)
    description = Column(Text)
    base_url = Column(String, nullable=True)
    corpus_path = Column(String, nullable=True)
    document_count = Column(Integer, default=0)
    last_ingested_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


class ScrapeRecord(Base):
    """Phase 8: Track scraped circulars to avoid duplicate ingestion."""
    __tablename__ = "scrape_records"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    regulator = Column(String, index=True)
    title = Column(String)
    source_url = Column(String, unique=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    status = Column(String, default="pending")  # pending | indexed | failed
    error_message = Column(Text, nullable=True)

# Phase 6: Enterprise DB Migrations (replacing CHAT_MEMORY dict)
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String, index=True)   # Links to document_id or explicit session
    role = Column(String)                     # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    department = Column(String)
    status = Column(String, default="pending") # pending, completed
    priority = Column(String, default="Medium") # low, medium, high
    deadline = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    document = relationship("Document", back_populates="tasks")
    assignee = relationship("User")

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    timestamp = Column(String)
    agent = Column(String)
    action = Column(String)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    timestamp = Column(String)
    event = Column(String)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    title = Column(String)
    severity = Column(String)
    created_at = Column(String)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)


class AgentGraphState(Base):
    __tablename__ = "agent_graph_states"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    document_id = Column(String, index=True)
    step_name = Column(String)
    state_data = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

