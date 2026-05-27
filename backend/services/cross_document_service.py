"""
Phase 9 — Cross-Document Reasoning
Compare and contrast multiple regulations without cross-contamination.
"""
from typing import Any, Dict, List, Optional, Union

from rag.hybrid_search import hybrid_search_and_rerank
from services.gemini_service import generate_text
from services.enterprise_answer_synthesizer import merge_retrieved_context
from database.database import SessionLocal
from database.models import Document


def _fetch_doc_names(doc_ids: List[str]) -> Dict[str, str]:
    db = SessionLocal()
    names = {}
    for doc_id in doc_ids:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            names[doc_id] = doc.filename
    db.close()
    return names


def compare_regulations(
    doc_ids: List[str],
    query: str = "compliance obligations conflicts and governance differences",
) -> Dict[str, Any]:
    """
    Retrieve from each document in isolation, then synthesize a cross-regulation comparison.
    """
    if len(doc_ids) < 2:
        raise ValueError("At least two document IDs are required for cross-document reasoning")

    doc_names = _fetch_doc_names(doc_ids)
    per_doc_context: List[str] = []

    for doc_id in doc_ids:
        chunks = hybrid_search_and_rerank(query, final_k=4, doc_id=doc_id)
        labeled = []
        fname = doc_names.get(doc_id, doc_id[:8])
        for chunk in chunks:
            section = chunk["metadata"].get("section_title", "General")
            labeled.append(f"[Document: {fname} | Section: {section}]\n{chunk['text']}")
        if labeled:
            per_doc_context.append(
                f"=== REGULATION: {fname} (ID: {doc_id}) ===\n"
                + merge_retrieved_context(labeled, max_chars=4000)
            )

    if len(per_doc_context) < 2:
        return {
            "document_ids": doc_ids,
            "comparison": "Insufficient indexed content in one or more documents.",
            "conflicts": [],
            "governance_differences": [],
        }

    combined = "\n\n".join(per_doc_context)
    prompt = f"""You are a regulatory intelligence analyst comparing multiple banking regulations.

Analyze the documents below and return a structured comparison in Markdown with these sections:
## Governance Differences
## Conflicting Controls
## Cybersecurity Obligations Comparison
## Unified Compliance Recommendation

Be specific. Cite which regulation (by document name) each point refers to.

--- DOCUMENTS ---
{combined[:14000]}
"""
    comparison = generate_text(prompt)

    conflict_prompt = f"""From this cross-regulation analysis, list ONLY conflicting controls.
Return valid JSON: {{"conflicts":[{{"control","doc_a_position","doc_b_position","severity"}}]}}
Context:
{combined[:6000]}
"""
    from services.ai_json import parse_json_with_retry, to_list, get_str

    conflict_data = parse_json_with_retry(conflict_prompt, schema_hint="conflicts array")
    conflicts = []
    for c in to_list(conflict_data.get("conflicts")):
        if isinstance(c, dict):
            conflicts.append({
                "control": get_str(c.get("control")),
                "doc_a_position": get_str(c.get("doc_a_position")),
                "doc_b_position": get_str(c.get("doc_b_position")),
                "severity": get_str(c.get("severity"), "Medium"),
            })

    return {
        "document_ids": doc_ids,
        "document_names": list(doc_names.values()),
        "comparison": comparison,
        "conflicts": conflicts,
        "governance_differences": _extract_section(comparison, "Governance Differences"),
    }


def _extract_section(text: str, heading: str) -> List[str]:
    lines = text.split("\n")
    bullets = []
    in_section = False
    for line in lines:
        if heading.lower() in line.lower():
            in_section = True
            continue
        if in_section and line.startswith("##"):
            break
        if in_section and line.strip().startswith(("-", "•", "*")):
            bullets.append(line.strip().lstrip("-•* ").strip())
    return bullets[:10]
