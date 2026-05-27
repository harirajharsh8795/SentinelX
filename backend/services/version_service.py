from typing import Dict, Any
from database.database import SessionLocal
from database.models import Document
from services.gemini_service import generate_text
import re

def compare_documents(doc_id_1: str, doc_id_2: str) -> Dict[str, Any]:
    db = SessionLocal()
    doc1 = db.query(Document).filter(Document.id == doc_id_1).first()
    doc2 = db.query(Document).filter(Document.id == doc_id_2).first()
    db.close()

    if not doc1 or not doc2:
        raise ValueError("One or both documents not found")

    # In a real system, we'd retrieve all text chunks or a pre-generated summary. 
    # For this system, let's use the local file text.
    text1 = extract_sample_text(doc1.file_path)
    text2 = extract_sample_text(doc2.file_path)

    prompt = f"""You are an expert compliance analyst.
Compare the following two versions of a regulatory circular and highlight EXACTLY what has changed.
Format your response with the following sections (use Markdown):
**Added:**
**Removed:**
**Modified:**
**Business Impact:**

--- VERSION 1 ({doc1.filename}) ---
{text1[:15000]}

--- VERSION 2 ({doc2.filename}) ---
{text2[:15000]}
"""
    try:
        comparison_result = generate_text(prompt)
    except Exception as e:
        comparison_result = f"Error generating comparison: {str(e)}"

    return {
        "doc_1": doc1.filename,
        "doc_2": doc2.filename,
        "comparison": comparison_result
    }

def extract_sample_text(path: str) -> str:
    from pypdf import PdfReader
    try:
        reader = PdfReader(path)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception:
        return "Could not extract text."
