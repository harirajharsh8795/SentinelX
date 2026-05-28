from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from models.schemas import (
    UploadResponse,
    AnalysisResponse,
    DashboardResponse,
    TaskListResponse,
    AlertListResponse,
    AgentLogListResponse,
    AuditTrailResponse,
    ChatRequest,
    ChatResponse,
    KnowledgeGraphResponse,
    CrossDocumentRequest,
    CorpusIngestRequest,
    ScrapeRunRequest,
    DocumentListResponse,
)
from services.corpus_ingestion_service import (
    ingest_all_corpus,
    ingest_corpus_source,
    get_corpus_stats,
    search_corpus,
    seed_regulatory_sources,
)
from services.live_ingestion_service import run_live_ingestion, get_scrape_status
from services.corpus_registry import REGULATORY_SOURCES
from services.document_service import ingest_document, analyze_document
from services.task_service import get_tasks
from services.log_service import get_agent_logs, get_audit_trail, get_alerts, get_dashboard
from services.chat_service import chat_with_document
from services.graph_service import generate_knowledge_graph, get_node_detail
from services.version_service import compare_documents
from services.report_service import (
    generate_compliance_report_csv,
    generate_executive_pdf,
    generate_board_docx,
)
from services.observability_service import get_traces, get_metrics
from services.analytics_service import get_predictive_analytics
from services.cross_document_service import compare_regulations
from fastapi.responses import PlainTextResponse, Response

from api.auth import get_current_active_user

router = APIRouter()

@router.post("/upload-document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), current_user = Depends(get_current_active_user)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads allowed")
    try:
        result = await ingest_document(file)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/documents", response_model=DocumentListResponse)
def get_documents_api(current_user = Depends(get_current_active_user)):
    from database.database import get_db_context
    from database.models import Document
    from models.schemas import DocumentItem
    
    with get_db_context() as db:
        # Optimization: Select only required metadata columns to bypass loading massive analysis/graph JSON fields
        docs = db.query(
            Document.id,
            Document.filename,
            Document.upload_date,
            Document.status,
            Document.regulator,
            Document.framework,
            Document.pages
        ).order_by(Document.upload_date.desc()).all()
        result = [
            DocumentItem(
                id=d.id,
                filename=d.filename,
                upload_date=d.upload_date.isoformat() if d.upload_date else "",
                status=d.status,
                regulator=d.regulator,
                framework=d.framework,
                pages=d.pages or 0
            )
            for d in docs
        ]
    return {"documents": result}


@router.post("/analyze-document", response_model=AnalysisResponse)
async def analyze_document_api(doc_id: str, current_user = Depends(get_current_active_user)):
    if not doc_id.strip():
        raise HTTPException(status_code=400, detail="doc_id is required")
    result = await analyze_document(doc_id)
    return result

@router.get("/dashboard", response_model=DashboardResponse)
def dashboard_api(document_id: str = None, current_user = Depends(get_current_active_user)):
    return get_dashboard(document_id)

@router.get("/tasks", response_model=TaskListResponse)
def tasks_api(document_id: str = None, current_user = Depends(get_current_active_user)):
    return {"items": get_tasks(document_id)}

from pydantic import BaseModel
class TaskUpdate(BaseModel):
    status: str

@router.put("/tasks/{task_id}")
def update_task_status_api(task_id: str, payload: TaskUpdate, current_user = Depends(get_current_active_user)):
    from database.database import get_db_context
    from database.models import Task
    
    allowed_statuses = {"pending", "completed", "in-progress"}
    status_lower = payload.status.lower().strip().replace("_", "-")
    if status_lower not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(allowed_statuses)}")

    with get_db_context() as db:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = status_lower
        db.commit()
    return {"status": "success"}

@router.get("/alerts", response_model=AlertListResponse)
def alerts_api(document_id: str = None, current_user = Depends(get_current_active_user)):
    return {"items": get_alerts(document_id)}

@router.get("/agent-logs", response_model=AgentLogListResponse)
def agent_logs_api(document_id: str = None, current_user = Depends(get_current_active_user)):
    return {"items": get_agent_logs(document_id)}

@router.get("/audit-trail", response_model=AuditTrailResponse)
def audit_trail_api(document_id: str = None, current_user = Depends(get_current_active_user)):
    return {"items": get_audit_trail(document_id)}

@router.post("/chat", response_model=ChatResponse)
async def chat_api(request: ChatRequest, current_user = Depends(get_current_active_user)):
    if not request.document_id.strip():
        raise HTTPException(status_code=400, detail="document_id is required")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")
    
    result = await chat_with_document(request.document_id, request.message)
    return result

@router.get("/knowledge-graph/{document_id}", response_model=KnowledgeGraphResponse)
async def knowledge_graph_api(document_id: str, current_user = Depends(get_current_active_user)):
    import asyncio
    if not document_id.strip():
        raise HTTPException(status_code=400, detail="document_id is required")
    result = await asyncio.to_thread(generate_knowledge_graph, document_id)
    return result


@router.get("/knowledge-graph/{document_id}/node/{node_id}")
async def knowledge_graph_node_api(document_id: str, node_id: str, current_user = Depends(get_current_active_user)):
    import asyncio
    detail = await asyncio.to_thread(get_node_detail, document_id, node_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Node not found")
    return detail

# Phase 9: Document Versioning & Temporal Analysis
@router.get("/compare-documents")
async def compare_documents_api(doc1: str, doc2: str, current_user = Depends(get_current_active_user)):
    if not doc1 or not doc2:
        raise HTTPException(status_code=400, detail="Both doc1 and doc2 IDs are required")
    try:
        return compare_documents(doc1, doc2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Phase 10: Audit Trails & Compliance Reporting
@router.get("/reports/compliance", response_class=PlainTextResponse)
def get_compliance_report(document_id: str = None, current_user = Depends(get_current_active_user)):
    csv_data = generate_compliance_report_csv(document_id)
    return PlainTextResponse(content=csv_data, headers={
        "Content-Disposition": f"attachment; filename=compliance_report_{document_id or 'latest'}.csv",
        "Content-Type": "text/csv"
    })

@router.get("/reports/executive-pdf")
def get_executive_pdf_report(document_id: str = None, current_user = Depends(get_current_active_user)):
    try:
        pdf_bytes = generate_executive_pdf(document_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=executive_compliance_report_{document_id or 'latest'}.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/reports/board-docx")
def get_board_docx_report(document_id: str = None, current_user = Depends(get_current_active_user)):
    try:
        docx_bytes = generate_board_docx(document_id)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=board_compliance_summary_{document_id or 'latest'}.docx"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/chat/history/{session_id}")
def chat_history_api(session_id: str, current_user = Depends(get_current_active_user)):
    from services.chat_service import get_chat_history
    from database.database import get_db_context
    from database.models import ChatMessage
    
    with get_db_context() as db:
        msgs = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(50).all()
        messages_list = [{"role": m.role, "content": m.content} for m in msgs]
        
    return {
        "session_id": session_id,
        "messages": messages_list,
        "history_preview": get_chat_history(session_id),
    }

@router.get("/observability/metrics")
def observability_metrics_api(current_user = Depends(get_current_active_user)):
    return get_metrics()

@router.get("/observability/traces")
def observability_traces_api(limit: int = 50, operation: str = None, current_user = Depends(get_current_active_user)):
    return {"traces": get_traces(limit=limit, operation=operation)}

# Phase 13: Advanced Analytics
@router.get("/analytics")
def analytics_api(document_id: str = None, current_user = Depends(get_current_active_user)):
    return get_predictive_analytics(document_id)

# Phase 9: Cross-Document Reasoning
@router.post("/compare-regulations")
async def compare_regulations_api(payload: CrossDocumentRequest, current_user = Depends(get_current_active_user)):
    if len(payload.document_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 document IDs")
    try:
        return compare_regulations(
            payload.document_ids,
            payload.query or "compliance obligations conflicts and governance differences",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

# Phase 7: Master Regulatory Corpus
@router.get("/corpus/sources")
def corpus_sources_api(current_user = Depends(get_current_active_user)):
    seed_regulatory_sources()
    return {
        "sources": [
            {
                "code": s.code,
                "name": s.name,
                "framework": s.framework,
                "description": s.description,
                "base_url": s.base_url,
            }
            for s in REGULATORY_SOURCES
        ]
    }

@router.get("/corpus/stats")
def corpus_stats_api(current_user = Depends(get_current_active_user)):
    return get_corpus_stats()

@router.post("/corpus/ingest")
def corpus_ingest_api(payload: CorpusIngestRequest, current_user = Depends(get_current_active_user)):
    try:
        if payload.source_code:
            return ingest_corpus_source(payload.source_code.upper(), force=payload.force)
        return ingest_all_corpus(force=payload.force)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/corpus/search")
def corpus_search_api(q: str, regulator: str = None, top_k: int = 5, current_user = Depends(get_current_active_user)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query q is required")
    return {"query": q, "results": search_corpus(q, regulator=regulator, top_k=top_k)}

# Phase 8: Live Scraping & Auto-Indexing
@router.post("/scrape/run")
async def scrape_run_api(payload: ScrapeRunRequest = ScrapeRunRequest(), current_user = Depends(get_current_active_user)):
    return await run_live_ingestion(payload.regulators)

@router.get("/scrape/status")
def scrape_status_api(current_user = Depends(get_current_active_user)):
    return get_scrape_status()

# Voice-Enabled Speech-to-Text Transcription Route
@router.post("/voice/transcribe")
async def transcribe_voice_api(file: UploadFile = File(...), current_user = Depends(get_current_active_user)):
    try:
        content = await file.read()
        import os
        from services.voice_service import transcribe_audio_bytes
        # Dynamically determine file extension to avoid whisper decoding issues
        ext = os.path.splitext(file.filename)[1] or ".webm"
        transcription = transcribe_audio_bytes(content, ext)
        return {"text": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ==============================================================================
# TELEMETRY — Real-time event feed (REST fallback for initial page load)
# ==============================================================================
@router.get("/telemetry")
async def get_telemetry(limit: int = 20, current_user = Depends(get_current_active_user)):
    """Returns recent real system events for Dashboard AI Telemetry panel."""
    from services.event_broadcaster import event_bus
    return {"events": event_bus.get_recent_events(limit=limit)}
