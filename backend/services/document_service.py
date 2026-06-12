import os
import re
import unicodedata
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
from utils.logger import get_logger
logger = get_logger(__name__)
from services.event_broadcaster import event_bus, EventLogger  # Real-time telemetry
from rag.chunker import chunk_text
from rag.hybrid_search import hybrid_search_and_rerank
from rag.retriever import add_chunks
from ai_agents.agent_graph import run_autonomous_compliance_graph
from services.enterprise_answer_synthesizer import merge_retrieved_context
from services.log_service import add_agent_logs, add_audit_events, add_alerts
from services.task_service import set_tasks_from_maps
from database.database import SessionLocal, get_db_context
from database.models import Document
from utils.pii_masking import mask_pii # Phase 12
def repair_hindi_text(text: str) -> str:
    """
    Repairs common Hindi (Devanagari) OCR corruption and extraction errors:
    - Fixes misplaced short 'i' matra (ि U+093F) which gets split or extracted in visual order.
    - Fixes misplaced spaces inside Hindi words (e.g., 'बैंक िंग' -> 'बैंकिंग').
    - Fixes common spelling corruptions in regulatory terms.
    """
    if not text:
        return ""
        
    # 1. Direct replacements for specific words and common phrases
    replacements = {
        "भारतीय रज़वर् ब क": "भारतीय रिज़र्व बैंक",
        "भारतीय रज़र्व ब क": "भारतीय रिज़र्व बैंक",
        "भारतीय रज़र्व बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रिज़र्व ब क": "भारतीय रिज़र्व बैंक",
        "भारतीय रज़वर् बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रिज़वर् बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रज़रर्व बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रज़रव् बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रज़र्व बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रिज़र्व बैंक": "भारतीय रिज़र्व बैंक",
        "भारतीय रिज़र्व बँक": "भारतीय रिज़र्व बैंक",
        "भारतीय रिजर्व बैंक": "भारतीय रिज़र्व बैंक",
        "रिजर्व बैंक": "रिज़र्व बैंक",
        "रज़र्व बैंक": "रिज़र्व बैंक",
        "रज़र्व बैंक": "रिज़र्व बैंक",
        "रिजर्व बक": "रिज़र्व बैंक",
        "रज़र्व बक": "रिज़र्व बैंक",
        "रज़वर्": "रिज़र्व",
        "ब क": "बैंक",
        "बँक": "बैंक",
        "बंक": "बैंक",
        "बॅक": "बैंक",
        "बैंक क": "बैंकिंग",
        "बैंक िंग": "बैंकिंग",
        "बैंक ग": "बैंकिंग",
        "ववभाग": "विभाग",
        "पररपत्र": "परिपत्र",
        "ववननयम": "विनियम",
        "ववननयमी": "विनियामक",
        "वववेकाधीन": "विवेकाधीन",
        "ववकास": "विकास",
        "ववक़ास": "विकास",
        "पररचालन": "परिचालन",
        "तनदे श": "निर्देश",
        "तनदे शों": "निर्देशों",
        "तनदे शका": "निर्देशिका",
        "सरक ुलर": "सर्कुलर",
        "स ब": "सेबी",
        "प्रौद्योगगकी": "प्रौद्योगिकी",
        "अधधकारी": "अधिकारी",
        "ननयोजन": "नियोजन",
        "ननयम": "नियम",
        "ननयमों": "नियमों",
        "ननरं तर": "निरंतर",
        "ननणरय": "निर्णय",
        "पररसीमा": "परिसीमा",
        "पररवतर्न": "परिवर्तन",
        "पररवार": "परिवार",
        "पररणाम": "परिणाम",
        "पररकल्पना": "परिकल्पना",
        "पररचय": "परिचय",
        "पररशद": "परिषद",
        "पररस्थिनत": "परिस्थिति",
        "वित्तीय": "वित्तीय",
        "द्ववतीय": "द्वितीय",
        "अननवायर्": "अनिवार्य",
        "सनमनत": "समिति",
        "गनतववधध": "गतिविधि",
        "गनतववधधयों": "गतिविधियों",
        "प्राधधकरण": "प्राधिकरण",
        "धनशोधन": "धनशोधन",
        "सुववधा": "सुविधा",
        "सूनचत": "सूचित",
        "सूरक्षत": "सुरक्षित",
        "सीमाएं": "सीमाएं",
        "सोननत": "सीमित",
        "सनत": "सीमित",
        "सूरक्षा": "सुरक्षा",
        "अनतररक्त": "अतिरिक्त",
        "सूनचका": "सूची",
    }
    
    for corrupted, corrected in replacements.items():
        text = text.replace(corrupted, corrected)
        
    # 2. General regex-based repairs for character corruption
    # Misplaced short 'i' matra - if extracted visually before consonant/conjunct, swap to correct Unicode order
    text = re.sub(r'(?<![\u0915-\u0939\u093c\u094d])ि\s*([\u0915-\u0939](?:\u094d[\u0915-\u0939])?)', r'\1ि', text)
    # Fix spaces around matras
    text = re.sub(r'([\u0915-\u0939])\s+ि', r'\1ि', text)
    # Fix separated anusvara (e.g. "बैं क" -> "बैंक")
    text = re.sub(r'([\u0900-\u097F])\s+ं', r'\1ं', text)
    
    # Common double-व U+0935 corruption to U+093F matra: U+0935 + U+0935 (वव) -> U+0935 + U+093F (वि)
    text = re.sub(r'\bवव', r'वि', text)
    text = re.sub(r'वव([\u0900-\u097F])', r'वि\1', text)
    
    # Same for "रर" -> "रि" (e.g. "परर" -> "परि")
    text = re.sub(r'रर', r'रि', text)
    
    # Same for "धध" -> "धि" (e.g. "अधध" -> "अधि")
    text = re.sub(r'धध', r'धि', text)

    # Same for "नन" -> "नि" (e.g. "ननयम" -> "नियम")
    text = re.sub(r'नन', r'नि', text)
    
    # Same for "तत" -> "ti"
    text = re.sub(r'तत', r'ति', text)

    # Fix space before matras or signs
    text = re.sub(r'\s+([ािीुूृेैोौंः्])', r'\1', text)

    return text


def normalize_text(text: str) -> str:
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    # Multiple spaces (preserving newlines for layout/headings)
    text = re.sub(r'[^\S\r\n]+', ' ', text)
    # Soft hyphens remove
    text = text.replace('\u00ad', '')
    # Hindi text repair
    text = repair_hindi_text(text)
    return text.strip()

def clean_extracted_text(text: str) -> str:
    """Phase 5: Enhanced OCR & Chunk Cleanup Pipeline."""
    if not text:
        return ""
    # 1. Normalize unicode characters (Use NFC instead of NFKC to preserve Devanagari conjuncts)
    text = unicodedata.normalize("NFC", text)
    
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
    
    # 8. Hindi text repair
    text = repair_hindi_text(text)
    
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


def extract_ocr_fallback(pdf_path: str) -> str:
    """Attempts local Tesseract OCR or falls back to raising an air-gapped environment error."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        logger.info(f"Triggering local Tesseract OCR fallback for: {pdf_path}")
        images = convert_from_path(pdf_path)
        pages_text = []
        for i, image in enumerate(images):
            try:
                # English + Hindi OCR
                text = pytesseract.image_to_string(image, lang="eng+hin")
            except Exception:
                text = pytesseract.image_to_string(image, lang="eng")
            pages_text.append(text)
        
        final_text = "\n".join(pages_text)
        final_text = unicodedata.normalize("NFC", final_text)
        return repair_hindi_text(final_text)
    except Exception as e:
        logger.warning(f"Local Tesseract OCR fallback failed or dependencies missing: {e}")
        raise ValueError(
            "PDF text extraction yielded no content. Local OCR dependencies (tesseract, pytesseract, pdf2image) "
            "are not fully configured on this machine."
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
            logger.info(f"pypdf returned empty text for {filename}, triggering OCR fallback...")
            try:
                text = extract_ocr_fallback(path)
            except Exception as ocr_err:
                logger.warning(f"OCR fallback failed: {ocr_err}")
                raise ocr_err
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            
    return text


def delete_all_existing_documents(db):
    from database.models import Document, ChatMessage, Task, Alert, AgentGraphState
    from vector_db.chroma_client import get_client
    
    old_docs = db.query(Document).all()
    for old_doc in old_docs:
        logger.info(f"Automatically deleting old document: {old_doc.filename} ({old_doc.id})")
        # 1. Delete file from local filesystem
        try:
            if old_doc.file_path and os.path.exists(old_doc.file_path):
                os.remove(old_doc.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete old file {old_doc.file_path}: {e}")
            
        # 2. Delete ChromaDB collection
        try:
            client = get_client()
            client.delete_collection(name=old_doc.id)
        except Exception as e:
            logger.warning(f"Failed to delete Chroma collection {old_doc.id}: {e}")
            
        # 3. Delete related database records
        try:
            db.query(ChatMessage).filter(ChatMessage.session_id == old_doc.id).delete()
            db.query(Task).filter(Task.document_id == old_doc.id).delete()
            db.query(Alert).filter(Alert.document_id == old_doc.id).delete()
            db.query(AgentGraphState).filter(AgentGraphState.document_id == old_doc.id).delete()
        except Exception as e:
            logger.warning(f"Failed to delete related records for {old_doc.id}: {e}")
        
        db.delete(old_doc)


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



    from services.event_broadcaster import event_bus
    event_bus.emit("system_info", f"Starting ingestion for corpus file: {filename}", doc_id=doc_id)

    with open(filepath, "rb") as src:
        content = src.read()
    if not content:
        raise ValueError("Empty file")

    with open(save_path, "wb") as f:
        f.write(content)

    from io import BytesIO
    storage_uri = storage_client.upload_fileobj(BytesIO(content), safe_name)
    event_bus.emit("system_info", f"File saved locally and uploaded to cloud storage.", doc_id=doc_id)

    text = _extract_text_from_file(save_path, safe_name)
    event_bus.emit("system_info", f"Text extraction complete. Total chars: {len(text)}", doc_id=doc_id)
    text = clean_extracted_text(text)
    text = sanitize_document_text(text, source_label=f"ingest_path:{safe_name}")  # Security: strip injections
    text = mask_pii(text)
    event_bus.emit("system_info", f"Text normalization, sanitization, and PII masking complete.", doc_id=doc_id)

    if not text.strip():
        raise ValueError(f"No extractable text from {filename}")

    if not regulator:
        regulator = detect_regulator(text, safe_name)

    chunks = chunk_text(normalize_text(text))
    if not chunks:
        raise ValueError("No indexable text extracted from document. PDF may be scanned/image-only.")
    event_bus.emit("system_info", f"Semantic chunking complete. Generated {len(chunks)} chunks.", doc_id=doc_id)
    
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


def ingest_document(file) -> Dict[str, Any]:
    ensure_upload_dir(settings.upload_dir)
    safe_name = sanitize_filename(file.filename)
    doc_id = str(uuid4())
    save_path = os.path.join(settings.upload_dir, f"{doc_id}-{safe_name}")



    from services.event_broadcaster import event_bus
    event_bus.emit("system_info", f"Initializing secure upload for {safe_name}...", doc_id=doc_id)

    content = file.file.read()
    if not content:
        raise ValueError("Empty file uploaded")
    if len(content) > 15 * 1024 * 1024:
        raise ValueError("File too large (max 15MB)")
    with open(save_path, "wb") as f:
        f.write(content)

    from io import BytesIO
    storage_uri = storage_client.upload_fileobj(BytesIO(content), safe_name)
    event_bus.emit("system_info", f"Secure upload complete. Storage URI: {storage_uri}", doc_id=doc_id)

    event_bus.emit("system_info", "Extracting text from PDF...", doc_id=doc_id)
    text = _extract_text_from_file(save_path, safe_name)
    event_bus.emit("system_info", f"Text extraction complete. Total character count: {len(text)}", doc_id=doc_id)
    
    text = clean_extracted_text(text)
    text = sanitize_document_text(text, source_label=f"upload:{safe_name}")  # Security: strip injections
    text = mask_pii(text)
    event_bus.emit("system_info", "Text cleaning and sanitization complete.", doc_id=doc_id)

    if not text.strip():
        raise ValueError("No extractable text or content found in uploaded PDF.")

    regulator = detect_regulator(text, safe_name)
    chunks = chunk_text(normalize_text(text))
    event_bus.emit("system_info", f"Semantic chunking complete. Generated {len(chunks)} chunks.", doc_id=doc_id)
    
    EventLogger.log_embedding_started(doc_id, safe_name, len(chunks))
    add_chunks(
        doc_id,
        chunks,
        regulator=regulator,
        ingestion_type="upload",
        document_name=safe_name,
    )

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
    EventLogger.log_embedding_completed(doc_id, safe_name)
    event_bus.emit("system_info", "Document indexed and saved successfully.", doc_id=doc_id)

    return {
        "document_id": doc_id,
        "filename": safe_name,
        "pages": len(chunks),
        "storage_uri": storage_uri,
        "regulator": regulator,
        "message": "Document ingested and indexed"
    }


def ingest_bytes(
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



    from services.event_broadcaster import event_bus
    event_bus.emit("system_info", f"Ingesting scraped file: {filename}", doc_id=doc_id)

    if not content:
        raise ValueError("Empty content")
    with open(save_path, "wb") as f:
        f.write(content)

    from io import BytesIO
    storage_uri = storage_client.upload_fileobj(BytesIO(content), safe_name)

    text = _extract_text_from_file(save_path, safe_name)
    text = clean_extracted_text(text)
    text = sanitize_document_text(text, source_label=f"scrape:{safe_name}")  # Security: strip injections
    text = mask_pii(text)

    if not text.strip():
        raise ValueError("No extractable text from downloaded file")

    if not regulator:
        regulator = detect_regulator(text, safe_name)

    chunks = chunk_text(normalize_text(text))
    
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
    EventLogger.log_embedding_completed(doc_id, safe_name)

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

        # Retrieve from cache if exists (with audit & repair logic)
        if doc_db.analysis_result:
            res_dict = dict(doc_db.analysis_result)
            maps = list(res_dict.get("maps", []))
            risks = res_dict.get("risks", [])
            
            # Schema Migration: Ensure executive_insights contains the structured 11-section corporate intelligence JSON
            exec_insights = res_dict.get("executive_insights", "")
            is_valid_structured_intel = False
            if exec_insights:
                try:
                    import json
                    parsed_intel = json.loads(exec_insights)
                    if isinstance(parsed_intel, dict) and "compliance_posture" in parsed_intel and "remediation_roadmap" in parsed_intel:
                        is_valid_structured_intel = True
                except Exception:
                    pass
            
            if not is_valid_structured_intel:
                from services.enterprise_answer_synthesizer import generate_fallback_executive_intelligence
                import json
                synthesis = generate_fallback_executive_intelligence(maps, risks, doc_db.filename or "")
                res_dict["executive_insights"] = json.dumps(synthesis)
                res_dict["synthesis"] = synthesis
                res_dict["summary"] = synthesis.get("executive_summary", {}).get("overview", "")
                doc_db.analysis_result = res_dict
                db.commit()
            
            # Ensure every risk has a corresponding directive (MAP)
            if risks:
                has_updated = False
                for r in risks:
                    risk_title = r.get("risk", "")
                    source_sec = r.get("source_section", "")
                    severity = r.get("severity", "Medium")
                    mitigation = r.get("mitigation", "")
                    
                    has_match = False
                    for m in maps:
                        m_sec = m.get("source_section", "") or ""
                        m_title = m.get("title", "") or ""
                        if source_sec and m_sec and (source_sec.lower() in m_sec.lower() or m_sec.lower() in source_sec.lower()):
                            has_match = True
                            break
                        if risk_title and m_title and (risk_title.lower() in m_title.lower() or m_title.lower() in risk_title.lower()):
                            has_match = True
                            break
                            
                    if not has_match:
                        # Auto-generate directive title directly from risk title and mitigation
                        r_lower = risk_title.lower()
                        if r_lower.startswith("missing "):
                            directive_title = f"Implement board-approved {risk_title[8:]}"
                        elif "lack of " in r_lower:
                            idx = r_lower.find("lack of ")
                            directive_title = f"Establish structured {risk_title[idx+8:]}"
                        elif r_lower.startswith("absence of "):
                            directive_title = f"Deploy required {risk_title[11:]}"
                        elif "failure to " in r_lower:
                            idx = r_lower.find("failure to ")
                            directive_title = f"Ensure compliance with requirement to {risk_title[idx+11:]}"
                        elif "non-compliance with " in r_lower:
                            idx = r_lower.find("non-compliance with ")
                            directive_title = f"Align controls with {risk_title[idx+20:]}"
                        else:
                            if mitigation and len(mitigation) < 80:
                                directive_title = mitigation
                            else:
                                directive_title = f"Remediate {risk_title}"
                        
                        # Classify department owner based on risk keywords
                        dept = "Compliance"
                        if any(w in r_lower for w in ["mfa", "cyber", "access", "technical", "encryption", "tls", "security", "it ", "system", "infrastructure"]):
                            dept = "IT & Cybersecurity"
                        elif any(w in r_lower for w in ["audit", "inspection", "verify", "reconcile", "reconciliation"]):
                            dept = "Internal Audit"
                        elif any(w in r_lower for w in ["aml", "money laundering", "str", "kyc", "customer identity"]):
                            dept = "AML Operations"
                        elif any(w in r_lower for w in ["transaction", "deposit", "payment", "limit", "operations"]):
                            dept = "Operations"
                            
                        deadline = "90 Days"
                        if severity.lower() == "high":
                            deadline = "Immediate"
                        elif severity.lower() == "medium":
                            deadline = "30 Days"
                            
                        citation = source_sec if source_sec else ("Relevant SEBI Clause" if "sebi" in (doc_db.filename or "").lower() else "Relevant RBI Clause")
                        
                        maps.append({
                            "title": directive_title[:200],
                            "department": dept,
                            "deadline": deadline,
                            "severity": severity,
                            "source_section": citation
                        })
                        has_updated = True
                
                if has_updated:
                    res_dict["maps"] = maps
                    doc_db.analysis_result = res_dict
                    db.commit()
                    
                    set_tasks_from_maps(maps, doc_id)
                
                from services.task_service import ensure_tasks_and_alerts_synced
                ensure_tasks_and_alerts_synced(db, doc_id)
                
            return res_dict


        regulator = doc_db.regulator or "RBI"  # Phase 3: capture for isolation

    queries = [
        "compliance obligations and timelines",
        "risk exposures and penalties",
        "audit requirements and reporting"
    ]
    context_chunks = []
    sources = []
    
    for query in queries:
        retrieved = await asyncio.to_thread(hybrid_search_and_rerank, query, final_k=6, doc_id=doc_id, regulator=regulator)
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
    
    # Run agent graph with 60-second hard timeout to prevent infinite hang
    agent_output = None
    try:
        agent_output = await asyncio.wait_for(
            run_autonomous_compliance_graph(doc_id, context),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"Agent graph timed out after 60s for doc {doc_id}. Recovering partial results.")
    except Exception as exc:
        logger.error(f"Graph execution failed: {exc}. Trying to retrieve partial results from db.")

    # If agent graph failed or timed out, recover partial results
    if agent_output is None:
        from database.models import AgentGraphState as DBGraphState
        from services.enterprise_answer_synthesizer import enrich_agent_output
        
        with get_db_context() as db:
            latest_state_db = db.query(DBGraphState).filter(
                DBGraphState.document_id == doc_id
            ).order_by(DBGraphState.timestamp.desc()).first()
            
            if latest_state_db and latest_state_db.state_data:
                state_data = latest_state_db.state_data
                logger.info(f"Successfully recovered partial state from step: {latest_state_db.step_name}")
                
                raw_output = {
                    "maps": state_data.get("maps", []),
                    "risks": state_data.get("risks", []),
                    "audit": state_data.get("audit", []),
                    "alerts": state_data.get("alerts", []),
                    "executive_insights": state_data.get("executive_insights", ""),
                    "agent_reasoning": state_data.get("agent_reasoning", []) + [
                        f"System recovered partial results from step '{latest_state_db.step_name}' after a model connection timeout."
                    ],
                    "conflicts": state_data.get("conflicts", [])
                }
                
                try:
                    enriched = enrich_agent_output(raw_output, context)
                except Exception:
                    enriched = raw_output
                    
                synthesis_dict = enriched.get("synthesis", {})
                summary_val = ""
                if isinstance(synthesis_dict, dict):
                    exec_sum = synthesis_dict.get("executive_summary", {})
                    if isinstance(exec_sum, dict):
                        summary_val = exec_sum.get("overview", "")
                    else:
                        summary_val = str(exec_sum)
                if not summary_val:
                    summary_val = enriched.get("executive_insights", "")

                agent_output = {
                    "document_id": doc_id,
                    "summary": summary_val,
                    "compliance_score": state_data.get("compliance_score", 100),
                    "risk_score": state_data.get("risk_score", 0),
                    "maps": enriched.get("maps", []),
                    "risks": enriched.get("risks", []),
                    "departments": list({m["department"] for m in enriched.get("maps", []) if "department" in m}),
                    "executive_insights": enriched.get("synthesis", {}).get("strategic_insights", "") or enriched.get("executive_insights", ""),
                    "agent_reasoning": enriched.get("agent_reasoning", []),
                    "grounding_confidence": round(state_data.get("grounding_score", 1.0), 2),
                    "hallucination_flag": state_data.get("grounding_score", 1.0) < 0.7,
                    "conflicts": state_data.get("conflicts", [])
                }
            else:
                logger.info("No partial states found. Constructing minimal baseline response.")
                agent_output = {
                    "document_id": doc_id,
                    "summary": "AI processing on Jetson hardware was interrupted, but context has been indexed. Please use the Copilot chat to query specific compliance requirements.",
                    "compliance_score": 100,
                    "risk_score": 0,
                    "maps": [
                        {
                            "title": "Review regulatory obligations and verify compliance control alignment",
                            "department": "Compliance",
                            "deadline": "within 90 days",
                            "severity": "Medium",
                            "source_section": "General",
                            "confidence": 0.60
                        }
                    ],
                    "risks": [
                        {
                            "risk": "Lapse in regulatory validation tracking",
                            "severity": "Medium",
                            "reason": "AI analysis was unable to complete full graph validation due to resource constraints.",
                            "source_section": "General"
                        }
                    ],
                    "departments": ["Compliance"],
                    "executive_insights": "**Business Implications**\nEnsure manual review of key paragraphs is performed.\n\n**Governance Responsibilities**\nCompliance officer should check the document status.",
                    "agent_reasoning": ["Orchestrator: Analysis timed out. Minimal baseline fallback generated."],
                    "grounding_confidence": 1.0,
                    "hallucination_flag": False,
                    "conflicts": []
                }

    # Build final result with sources
    res_dict = {
        **agent_output,
        "sources": sources
    }

    # Ensure they are written to SQLite tasks and alerts (double-layer sync)
    async with db_write_lock:
        maps_to_sync = res_dict.get("maps", [])
        risks_to_sync = res_dict.get("risks", [])
        alerts_to_sync = res_dict.get("alerts", [])
        if not alerts_to_sync and risks_to_sync:
            alerts_to_sync = [
                f"Vulnerability risk alert: {r.get('risk')}" 
                for r in risks_to_sync
                if str(r.get("severity", "Medium")).lower() == "high"
            ]
            if not alerts_to_sync:
                alerts_to_sync = [
                    f"Vulnerability risk alert: {r.get('risk')}" 
                    for r in risks_to_sync
                ]
            res_dict["alerts"] = alerts_to_sync
        
        # Write tasks and alerts sequentially using threads
        if maps_to_sync:
            await asyncio.to_thread(set_tasks_from_maps, maps_to_sync, doc_id)
        if alerts_to_sync:
            def _sync_alerts():
                from database.models import Alert
                from uuid import uuid4
                from datetime import datetime, timezone
                with get_db_context() as db:
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
            await asyncio.to_thread(_sync_alerts)
            
        def _write_analysis_result():
            with get_db_context() as db:
                doc_db = db.query(Document).filter(Document.id == doc_id).first()
                if doc_db:
                    doc_db.analysis_result = res_dict
                    db.commit()
        await asyncio.to_thread(_write_analysis_result)

    # Run audit logs and knowledge graph in background (fire-and-forget)
    async def _background_post_analysis():
        try:
            async with db_write_lock:
                await asyncio.to_thread(
                    add_agent_logs,
                    ["Compliance Agent", "Risk Agent", "Workflow Agent", "Validation Agent", "Alert Agent", "Cross-Regulation Agent"],
                    document_id=doc_id
                )
                
                audit_notes = [f"Automated audit check passed with compliance score: {agent_output.get('compliance_score', 100)}%"]
                for risk in agent_output.get("risks", []):
                    audit_notes.append(f"Risk flagged: {risk.get('risk')} - severity: {risk.get('severity')}")
                await asyncio.to_thread(add_audit_events, audit_notes, document_id=doc_id)

                # Pre-generate knowledge graph in background to cache it
                from services.graph_service import generate_knowledge_graph
                await asyncio.to_thread(generate_knowledge_graph, doc_id)
        except Exception as e:
            logger.error(f"Background post-analysis failed: {e}")

    asyncio.create_task(_background_post_analysis())

    return res_dict


def reindex_all_documents() -> None:
    """
    Re-index all documents currently stored in the database.
    Reads each document's PDF file from the disk, extracts and repairs the text,
    re-chunks, and re-adds to ChromaDB.
    """
    from database.database import get_db_context
    from database.models import Document
    from vector_db.chroma_client import get_client
    
    with get_db_context() as db:
        docs = db.query(Document).all()
        if not docs:
            logger.info("No documents found to re-index.")
            return
            
        for doc in docs:
            logger.info(f"Re-indexing document: {doc.filename} ({doc.id})")
            if not doc.file_path or not os.path.exists(doc.file_path):
                logger.warning(f"File path not found or empty for document {doc.id}: {doc.file_path}")
                continue
                
            try:
                # 1. Extract, clean, and repair text
                text = _extract_text_from_file(doc.file_path, doc.filename)
                text = clean_extracted_text(text)
                text = sanitize_document_text(text, source_label=f"reindex:{doc.filename}")
                text = mask_pii(text)
                
                if not text.strip():
                    logger.warning(f"No extractable text found for document {doc.id} during re-indexing.")
                    continue
                # 2. Re-create collection in Chroma
                client = get_client()
                try:
                    from rag.retriever import sanitize_collection_name
                    client.delete_collection(name=sanitize_collection_name(doc.id))
                except Exception:
                    pass
                
                try:
                    from services.graph_service import invalidate_graph_cache
                    invalidate_graph_cache(doc.id)
                except Exception:
                    pass

                chunks = chunk_text(normalize_text(text))
                logger.info(f"Re-chunked document {doc.id} into {len(chunks)} chunks.")
                
                add_chunks(
                    doc.id,
                    chunks,
                    regulator=doc.regulator,
                    framework=doc.framework,
                    source_url=doc.source_url,
                    ingestion_type=doc.ingestion_type,
                    document_name=doc.filename,
                )
                
                # 3. Update database record page count
                doc.pages = len(chunks)
                db.commit()
                logger.info(f"Successfully re-indexed document {doc.filename}")
            except Exception as e:
                logger.error(f"Failed to re-index document {doc.id}: {e}")

