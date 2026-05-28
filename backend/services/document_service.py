import os
from uuid import uuid4
from typing import Dict, Any
import asyncio
from database.database import db_write_lock

from pypdf import PdfReader
from io import BytesIO

from utils.config import settings
from utils.security import ensure_upload_dir, sanitize_filename
from utils.storage import storage_client
from utils.input_sanitizer import sanitize_document_text  # Security: Prompt injection defense
from services.event_broadcaster import event_bus, EventLogger  # Real-time telemetry
from rag.chunker import chunk_text
from rag.hybrid_search import hybrid_search_and_rerank
from rag.retriever import add_chunks
from ai_agents.agent_graph import run_autonomous_compliance_graph
from services.enterprise_answer_synthesizer import merge_retrieved_context
from services.log_service import add_agent_logs, add_audit_events, add_alerts
from services.task_service import set_tasks_from_maps
from database.database import SessionLocal
from database.models import Document
from utils.pii_masking import mask_pii # Phase 12
import re
import unicodedata

def clean_extracted_text(text: str) -> str:
    """Phase 5: Enhanced OCR & Chunk Cleanup Pipeline."""
    if not text:
        return ""
    # 1. Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)
    
    # 2. Fix hyphenated word breaks (split words across lines)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # 3. Strip common page number patterns and headers/footers
    text = re.sub(r'(?i)\bpage\s+\d+(\s+of\s+\d+)?\b', '', text)
    # Strip lines that are just page numbers
    text = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', text)
    
    # 4. Remove standalone Roman numeral lines (e.g. "III.", "iv)", "XII")
    text = re.sub(r'(?m)^\s*[IVXLCDMivxlcdm]+[\.\)\s]*$', '', text)
    
    # 5. Strip running headers/footers (common in RBI/SEBI circulars)
    text = re.sub(r'(?im)^\s*(reserve bank of india|confidential|draft|page \d+|circular no\.?.*|dated:?\s*\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})\s*$', '', text)
    
    # 6. Remove lines with only repeated symbols (e.g. "---", "===", "***", "___")
    text = re.sub(r'(?m)^\s*[\-=\*_\.]{3,}\s*$', '', text)
    
    # 7. Eliminate OCR noise (carriage returns, excessive spaces, repeated symbols)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    
    return text.strip()

def detect_regulator(text: str, filename: str) -> str:
    fn = filename.upper()
    if "RBI" in fn:
        return "RBI"
    if "SEBI" in fn:
        return "SEBI"
    if "NPCI" in fn:
        return "NPCI"
    if "CERT" in fn or "CERT-IN" in fn or "CERTIN" in fn:
        return "CERT-IN"
    if "SBI" in fn:
        return "SBI"
    
    content = text.upper()
    if "RESERVE BANK OF INDIA" in content or " RBI " in content:
        return "RBI"
    if "SECURITIES AND EXCHANGE BOARD OF INDIA" in content or " SEBI " in content:
        return "SEBI"
    if "NATIONAL PAYMENTS CORPORATION OF INDIA" in content or " NPCI " in content:
        return "NPCI"
    if "INDIAN COMPUTER EMERGENCY RESPONSE TEAM" in content or "CERT-IN" in content or "CERTIN" in content:
        return "CERT-IN"
    if "STATE BANK OF INDIA" in content or " SBI " in content:
        return "SBI"
        
    return "RBI"  # Default fallback


def _find_saved_document_path(doc_id: str) -> str:
    ensure_upload_dir(settings.upload_dir)
    prefix = f"{doc_id}-"
    for filename in os.listdir(settings.upload_dir):
        if filename.startswith(prefix) and filename.lower().endswith(".pdf"):
            return os.path.join(settings.upload_dir, filename)
    return ""


def extract_ocr_with_gemini(pdf_path: str) -> str:
    """Offline Mode: Gemini OCR fallback is disabled."""
    logger.warning("Gemini OCR fallback is requested but disabled in local offline mode.")
    raise ValueError(
        "PDF text extraction yielded no content. OCR fallback is disabled in local offline mode "
        "to comply with air-gapped deployment restrictions."
    )


def _extract_text(path: str) -> str:
    reader = PdfReader(path)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text)


def _extract_text_from_file(path: str, filename: str) -> str:
    text = ""
    if filename.lower().endswith(".pdf"):
        try:
            text = _extract_text(path)
        except Exception as e:
            logger.warning(f"pypdf extraction failed for {filename}, attempting OCR: {e}")
            text = ""
            
        if not text.strip():
            logger.info(f"pypdf returned empty text for {filename}, triggering Gemini OCR fallback...")
            text = extract_ocr_with_gemini(path)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            
    return text


def ingest_file_from_path(
    filepath: str,
    regulator: str = None,
    framework: str = None,
    source_url: str = None,
    ingestion_type: str = "corpus",
    external_id: str = None,
) -> Dict[str, Any]:
    """
    Phase 7/8: Unified ingestion for corpus files, scraped PDFs, and manual uploads.
    """
    ensure_upload_dir(settings.upload_dir)
    filename = os.path.basename(filepath)
    safe_name = sanitize_filename(filename)
    doc_id = str(uuid4())
    save_path = os.path.join(settings.upload_dir, f"{doc_id}-{safe_name}")

    with open(filepath, "rb") as src:
        content = src.read()
    if not content:
        raise ValueError("Empty file")

    with open(save_path, "wb") as f:
        f.write(content)

    from io import BytesIO
    storage_uri = storage_client.upload_fileobj(BytesIO(content), safe_name)

    text = _extract_text_from_file(save_path, safe_name)
    text = clean_extracted_text(text)
    text = sanitize_document_text(text, source_label=f"ingest_path:{safe_name}")  # Security: strip injections
    text = mask_pii(text)

    if not text.strip():
        raise ValueError(f"No extractable text from {filename}")

    if not regulator:
        regulator = detect_regulator(text, safe_name)

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No indexable text extracted from document. PDF may be scanned/image-only.")
    EventLogger.log_embedding_started(doc_id, safe_name, len(chunks))
    add_chunks(
        doc_id,
        chunks,
        regulator=regulator,
        framework=framework,
        source_url=source_url,
        ingestion_type=ingestion_type,
        document_name=safe_name,
    )

    from database.database import get_db_context
    with get_db_context() as db:
        doc = Document(
            id=doc_id,
            filename=safe_name,
            file_path=save_path,
            storage_uri=storage_uri,
            pages=len(chunks),
            status="Indexed",
            regulator=regulator,
            framework=framework,
            source_url=source_url,
            ingestion_type=ingestion_type,
            external_id=external_id,
        )
        db.add(doc)
        db.commit()

    EventLogger.log_document_uploaded(doc_id, safe_name, f"{len(chunks)} chunks, regulator: {regulator}")
    EventLogger.log_embedding_completed(doc_id, safe_name)

    return {
        "document_id": doc_id,
        "filename": safe_name,
        "pages": len(chunks),
        "regulator": regulator,
        "framework": framework,
        "ingestion_type": ingestion_type,
        "message": "Document ingested and indexed",
    }


async def ingest_document(file) -> Dict[str, Any]:
    ensure_upload_dir(settings.upload_dir)
    safe_name = sanitize_filename(file.filename)
    doc_id = str(uuid4())
    save_path = os.path.join(settings.upload_dir, f"{doc_id}-{safe_name}")

    content = await file.read()
    if not content:
        raise ValueError("Empty file uploaded")
    if len(content) > 15 * 1024 * 1024:
        raise ValueError("File too large (max 15MB)")
    with open(save_path, "wb") as f:
        f.write(content)

    from io import BytesIO
    storage_uri = storage_client.upload_fileobj(BytesIO(content), safe_name)

    text = await asyncio.to_thread(_extract_text_from_file, save_path, safe_name)
    text = clean_extracted_text(text)
    text = sanitize_document_text(text, source_label=f"upload:{safe_name}")  # Security: strip injections
    text = mask_pii(text)

    if not text.strip():
        raise ValueError("No extractable text or content found in uploaded PDF.")

    regulator = detect_regulator(text, safe_name)
    chunks = chunk_text(text)
    await asyncio.to_thread(
        add_chunks,
        doc_id,
        chunks,
        regulator=regulator,
        ingestion_type="upload",
        document_name=safe_name,
    )

    from database.database import get_db_context
    with get_db_context() as db:
        doc = Document(
            id=doc_id,
            filename=safe_name,
            file_path=save_path,
            storage_uri=storage_uri,
            pages=len(chunks),
            status="Indexed",
            ingestion_type="upload",
            regulator=regulator,
        )
        db.add(doc)
        db.commit()

    return {
        "document_id": doc_id,
        "filename": safe_name,
        "pages": len(chunks),
        "storage_uri": storage_uri,
        "regulator": regulator,
        "message": "Document ingested and indexed"
    }


async def ingest_bytes(
    filename: str,
    content: bytes,
    regulator: str = None,
    framework: str = None,
    source_url: str = None,
    ingestion_type: str = "scrape",
    external_id: str = None,
) -> Dict[str, Any]:
    """Phase 8: Ingest downloaded PDF bytes from live scrapers."""
    ensure_upload_dir(settings.upload_dir)
    safe_name = sanitize_filename(filename)
    doc_id = str(uuid4())
    save_path = os.path.join(settings.upload_dir, f"{doc_id}-{safe_name}")

    if not content:
        raise ValueError("Empty content")
    with open(save_path, "wb") as f:
        f.write(content)

    from io import BytesIO
    storage_uri = storage_client.upload_fileobj(BytesIO(content), safe_name)

    text = await asyncio.to_thread(_extract_text_from_file, save_path, safe_name)
    text = clean_extracted_text(text)
    text = sanitize_document_text(text, source_label=f"scrape:{safe_name}")  # Security: strip injections
    text = mask_pii(text)

    if not text.strip():
        raise ValueError("No extractable text from downloaded file")

    if not regulator:
        regulator = detect_regulator(text, safe_name)

    chunks = chunk_text(text)
    await asyncio.to_thread(
        add_chunks,
        doc_id, chunks,
        regulator=regulator,
        framework=framework,
        source_url=source_url,
        ingestion_type=ingestion_type,
        document_name=safe_name,
    )

    from database.database import get_db_context
    with get_db_context() as db:
        doc = Document(
            id=doc_id,
            filename=safe_name,
            file_path=save_path,
            storage_uri=storage_uri,
            pages=len(chunks),
            status="Indexed",
            regulator=regulator,
            framework=framework,
            source_url=source_url,
            ingestion_type=ingestion_type,
            external_id=external_id,
        )
        db.add(doc)
        db.commit()

    return {
        "document_id": doc_id,
        "filename": safe_name,
        "pages": len(chunks),
        "regulator": regulator,
        "ingestion_type": ingestion_type,
        "message": "Scraped document ingested and indexed",
    }


async def analyze_document(doc_id: str) -> Dict[str, Any]:
    from database.database import get_db_context
    with get_db_context() as db:
        doc_db = db.query(Document).filter(Document.id == doc_id).first()
        
        if not doc_db:
            return {
                "document_id": doc_id,
                "summary": "Document not found",
                "compliance_score": 0,
                "risk_score": 0,
                "maps": [],
                "risks": [],
                "departments": [],
                "executive_insights": "",
                "agent_reasoning": [],
                "sources": []
            }

        # Retrieve from cache if exists
        if doc_db.analysis_result:
            return dict(doc_db.analysis_result)

        regulator = doc_db.regulator or "RBI"  # Phase 3: capture for isolation

    queries = [
        "compliance obligations and timelines",
        "risk exposures and penalties",
        "audit requirements and reporting"
    ]
    context_chunks = []
    sources = []
    
    for query in queries:
        retrieved = hybrid_search_and_rerank(query, final_k=6, doc_id=doc_id, regulator=regulator)
        for chunk in retrieved:
            # Reconstruct the string to inject metadata for citations
            section = chunk["metadata"].get("section_title", "General")
            c_text = chunk["text"]
            formatted_chunk = f"[Source Section: {section}]\n{c_text}"
            
            if formatted_chunk not in context_chunks:
                context_chunks.append(formatted_chunk)
                sources.append({
                    "section_title": section,
                    "snippet": c_text[:150] + "...",
                    "score": chunk.get("rerank_score", chunk.get("score", 0))
                })

    if not context_chunks:
        return {
            "document_id": doc_id,
            "summary": "No indexed content found for this document. Re-upload or re-index the PDF.",
            "compliance_score": 0,
            "risk_score": 0,
            "maps": [],
            "risks": [],
            "departments": [],
            "executive_insights": "",
            "agent_reasoning": ["Retrieval returned zero chunks — analysis aborted to prevent hallucination."],
            "sources": [],
        }

    context = merge_retrieved_context(context_chunks)
    # Security: Sanitize merged context before it enters LLM agent graph
    context = sanitize_document_text(context, source_label=f"analysis_context:{doc_id}")
    try:
        agent_output = await run_autonomous_compliance_graph(doc_id, context)
    except Exception as exc:
        return {
            "document_id": doc_id,
            "summary": f"AI analysis failed: {exc}",
            "compliance_score": 0,
            "risk_score": 0,
            "maps": [],
            "risks": [],
            "departments": [],
            "executive_insights": "",
            "agent_reasoning": [f"Failure during graph execution: {exc}"],
            "sources": []
        }

    # Add logs and audit details under db_write_lock
    async with db_write_lock:
        await asyncio.to_thread(
            add_agent_logs,
            ["Compliance Agent", "Risk Agent", "Workflow Agent", "Validation Agent", "Alert Agent", "Cross-Regulation Agent"],
            document_id=doc_id
        )
        
        audit_notes = [f"Automated audit check passed with compliance score: {agent_output['compliance_score']}%"]
        for risk in agent_output.get("risks", []):
            audit_notes.append(f"Risk flagged: {risk.get('risk')} - severity: {risk.get('severity')}")
        await asyncio.to_thread(add_audit_events, audit_notes, document_id=doc_id)

        # Pre-generate knowledge graph in background to cache it
        from services.graph_service import generate_knowledge_graph
        await asyncio.to_thread(generate_knowledge_graph, doc_id)

        res_dict = {
            **agent_output,
            "sources": sources
        }

        def _write_analysis_result():
            with get_db_context() as db:
                doc_db = db.query(Document).filter(Document.id == doc_id).first()
                if doc_db:
                    doc_db.analysis_result = res_dict
                    db.commit()
                    
        await asyncio.to_thread(_write_analysis_result)

    return res_dict

