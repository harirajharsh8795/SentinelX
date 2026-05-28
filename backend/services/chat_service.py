import os
from typing import Dict, List, Any
from rag.hybrid_search import hybrid_search_and_rerank
from services.gemini_service import generate_text
from database.database import get_db_context
from database.models import ChatMessage, Document
from utils.input_sanitizer import sanitize_document_text, sanitize_user_query  # Security
from database.database import SessionLocal

def get_chat_history(doc_id: str) -> str:
    from database.database import get_db_context
    with get_db_context() as db:
        history = db.query(ChatMessage).filter(ChatMessage.session_id == doc_id).order_by(ChatMessage.created_at.desc()).limit(6).all()
        if not history:
            return "No previous conversation."
        
        # Reverse to chronological
        history = history[::-1]
        
        formatted = []
        for msg in history:
            role = "User" if msg.role == "user" else "AI"
            formatted.append(f"{role}: {msg.content}")
        
    return "\n".join(formatted)

def rewrite_query(original_query: str, chat_history: str) -> str:
    """
    Semantic Query Rewriting Engine (Phase 1):
    1. Resolves pronouns using conversation history.
    2. Expands domain-specific terminology (V-CIP, CDD, FIU-IND, etc.).
    3. Adds compliance intent keywords (timelines, penalties, audit obligations).
    """
    # Even without history, expand domain terms for better retrieval
    expanded = _expand_domain_terms(original_query)

    if "No previous conversation" in chat_history:
        return expanded

    prompt = f"""You are a regulatory compliance search query optimizer for Indian banking.

TASK: Rewrite the user's query into a rich, standalone search query.

RULES:
1. Resolve all pronouns ("it", "this", "that") using conversation history.
2. Expand abbreviations: V-CIP → Video-based Customer Identification Process, CDD → Customer Due Diligence, STR → Suspicious Transaction Report, CTR → Cash Transaction Report, FIU-IND → Financial Intelligence Unit India, VAPT → Vulnerability Assessment and Penetration Testing, MFA → Multi-Factor Authentication, CISO → Chief Information Security Officer.
3. Add compliance intent keywords where relevant (e.g., timelines, deadlines, penalties, audit requirements, reporting obligations).
4. Keep the query under 120 words. Return ONLY the rewritten query text, nothing else.

--- PAST CONVERSATION HISTORY ---
{chat_history}

--- USER QUERY ---
{original_query}

Rewritten Query:"""
    try:
        rewritten = generate_text(prompt).strip()
        # Fallback if Gemini refuses or is verbose
        if "\n" in rewritten or len(rewritten) > 250:
            return expanded
        return rewritten
    except Exception:
        return expanded


# Phase 1: Domain-aware term expansion dictionary
_DOMAIN_EXPANSIONS = {
    "v-cip": "V-CIP Video-based Customer Identification Process remote onboarding KYC verification identity validation",
    "vcip": "V-CIP Video-based Customer Identification Process remote onboarding KYC verification",
    "cdd": "Customer Due Diligence CDD KYC risk profiling identity verification",
    "kyc": "Know Your Customer KYC identity verification onboarding due diligence CDD",
    "aml": "Anti-Money Laundering AML transaction monitoring suspicious activity STR CTR FIU-IND",
    "str": "Suspicious Transaction Report STR AML FIU-IND reporting obligation",
    "ctr": "Cash Transaction Report CTR AML FIU-IND threshold reporting",
    "fiu": "Financial Intelligence Unit FIU-IND AML STR CTR reporting",
    "fiu-ind": "Financial Intelligence Unit India FIU-IND AML STR reporting penalties",
    "vapt": "Vulnerability Assessment and Penetration Testing VAPT cybersecurity audit security testing",
    "mfa": "Multi-Factor Authentication MFA access control security two-factor",
    "ciso": "Chief Information Security Officer CISO governance cybersecurity leadership accountability",
    "uapa": "Unlawful Activities Prevention Act UAPA terror financing sanction screening",
    "tls": "Transport Layer Security TLS encryption data-in-transit HTTPS certificate",
    "ddos": "Distributed Denial of Service DDoS attack mitigation availability business continuity",
    "sla": "Service Level Agreement SLA vendor third-party outsourcing performance",
    "pii": "Personally Identifiable Information PII data privacy protection masking",
}


def _expand_domain_terms(query: str) -> str:
    """Expand abbreviated regulatory terms into rich search phrases."""
    q_lower = query.lower()
    expansions = []
    for abbrev, expansion in _DOMAIN_EXPANSIONS.items():
        if abbrev in q_lower:
            expansions.append(expansion)
    if expansions:
        return query + " " + " ".join(expansions[:3])  # Cap at 3 expansions
    return query

def append_to_memory(doc_id: str, role: str, content: str):
    from database.database import get_db_context
    with get_db_context() as db:
        msg = ChatMessage(session_id=doc_id, role=role, content=content)
        db.add(msg)
        db.commit()

def classify_question(query: str) -> str:
    """
    Question Classification:
    Categorizes the query into one of 9 distinct intents for targeted compliance prompting.
    """
    q = query.lower().strip()
    if any(w in q for w in ["governance", "board", "director", "management", "committee", "ciso", "roles", "responsibilities"]):
        return "governance"
    if any(w in q for w in ["vendor", "outsourcing", "third-party", "supplier", "partner", "procurement", "sla"]):
        return "vendor_risk"
    if any(w in q for w in ["deadline", "timeline", "when", "days", "months", "date", "schedule", "period"]):
        return "timelines"
    if any(w in q for w in ["penalty", "punishment", "fine", "violation", "non-compliance", "lawsuit", "prosecution", "sanction"]):
        return "penalties"
    if any(w in q for w in ["aml", "anti-money laundering", "money laundering", "transaction monitoring", "terrorist financing"]):
        return "aml"
    if any(w in q for w in ["kyc", "know your customer", "onboarding", "cdd", "due diligence", "identity", "verification"]):
        return "kyc"
    if any(w in q for w in ["cyber", "security", "hack", "breach", "network", "firewall", "access", "password", "mfa", "encryption", "vapt", "threat", "incident"]):
        return "cybersecurity"
    if any(w in q for w in ["audit", "inspector", "review", "check", "verify", "inspection", "log review"]):
        return "audit"
    if any(w in q for w in ["ops", "operation", "transaction", "process", "day-to-day", "settlement", "clearing", "reconciliation"]):
        return "operations"
    return "general"

def build_dynamic_prompt(category: str, chat_history: str, context_text: str, standalone_query: str, message: str, regulator: str) -> str:
    """
    Dynamic Prompt Engineering & Answer Formatter:
    Customizes prompts based on category and regulator.
    """
    regulator_guidelines = {
        "RBI": "RBI directives mandate data localization, security incident reporting timescales (2-6 hours), CISO oversight, and strict customer confidentiality.",
        "SEBI": "SEBI guidelines focus on investor safety, fiduciary accountability of board members, stock exchange disclosure timelines, and prevention of market manipulation.",
        "NPCI": "NPCI framework mandates UPI payment protocol security, merchant risk management, clearing settlement timelines, and transactional audit trails.",
        "CERT-IN": "CERT-IN directives strictly enforce national cybersecurity compliance, threat landscape response, and mandatory reporting of cybersecurity incidents within 6 hours.",
        "SBI": "SBI internal policies mandate strict risk assessment checks, operational workflow guidelines, branch control logs, and customer service SLAs.",
    }
    regulator_instruction = regulator_guidelines.get(regulator, "Standard national compliance and audit regulations apply.")

    base_instructions = f"""You are SentinelX, an expert enterprise compliance assistant.
Your goal is to answer the user's latest question with utmost accuracy based *strictly* on the document context provided below.

REGULATOR CONSTRAINTS ({regulator}):
{regulator_instruction}

CRITICAL RULES (Answer Grounding):
1. Answer ONLY from the retrieved context. Never hallucinate.
2. If the context does NOT contain the answer, explicitly state: "According to the document, I cannot find information regarding this."
3. CITE sources using the exact source number, e.g., "(Source 1)".
"""

    if category == "governance":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Governance Framework:** [Roles, committees, or organizational structures]
**Responsibility Allocation:** [Who is accountable for what]
**Source Citations:** [List references]"""
    elif category == "vendor_risk":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Third-Party Risks:** [Risks associated with outsourcing or vendors]
**Service Level Agreements (SLAs):** [SLA terms or vendor controls]
**Source Citations:** [List references]"""
    elif category == "timelines":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Compliance Timelines:** [Specific deadlines or frequencies]
**Action Timelines:** [Timeline associated actions]
**Source Citations:** [List references]"""
    elif category == "penalties":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Regulatory Violations:** [Non-compliance risks or infractions]
**Fines & Penalties:** [Amounts or sanctions defined]
**Source Citations:** [List references]"""
    elif category == "aml":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**AML Controls:** [Transaction monitoring or laundering checks]
**SOP & Screening:** [AML screening policies]
**Source Citations:** [List references]"""
    elif category == "kyc":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**KYC Procedures:** [Customer identification, verification steps]
**Customer Due Diligence (CDD):** [Requirements for CDD]
**Source Citations:** [List references]"""
    elif category == "cybersecurity":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Cybersecurity Controls:** [Access controls, MFA, firewall rules]
**Incident Response:** [Incident handling or threat prevention]
**Source Citations:** [List references]"""
    elif category == "audit":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Audit Requirements:** [Audit frequency, checklists, scope]
**Evidence & Logs:** [Audit log review parameters]
**Source Citations:** [List references]"""
    elif category == "operations":
        format_rules = """FORMAT YOUR ANSWER AS FOLLOWS:
**Operational Controls:** [Processing rules, day-to-day SOPs]
**Business Impact:** [Effect on banking operations]
**Source Citations:** [List references]"""
    else:
        format_rules = """FORMAT YOUR ANSWER STRICTLY AS FOLLOWS (with markdown bolding):
**Key Findings:**
• [Point 1]
• [Point 2]

**Business Impact:**
[Brief summary of what this means]

**Source Citations:**
• [Reference]"""

    prompt = f"""{base_instructions}

{format_rules}

--- PAST CONVERSATION HISTORY ---
{chat_history}

--- RETRIEVED DOCUMENT CONTEXT (For Query: {standalone_query}) ---
{context_text}

--- LATEST QUESTION ---
User: {message}

Remember to thoroughly VALIDATE your answer against the context before responding. Do not output repetitive generic responses.
AI Answer:
"""
    return prompt

def chat_with_document(doc_id: str, message: str) -> Dict[str, Any]:
    """
    Combines conversational memory, Query Rewriting, Question Classification, 
    and Hybrid MMR RAG Retrieval to answer contextually.
    """
    # 1. Resolve regulator constraint
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    regulator = doc.regulator if (doc and doc.regulator) else "RBI"
    db.close()

    # 2. Get past chat history (Step 13: Chat Memory)
    chat_history = get_chat_history(doc_id)
    
    # 3. Semantic Query Rewriting (Step 6)
    standalone_query = rewrite_query(message, chat_history)

    # Security: Sanitize user message before it enters any prompt
    safe_message = sanitize_user_query(message)
    
    # 4. Retrieve chunks with MMR enabled + strict regulator isolation (Phase 3)
    retrieved_chunks = hybrid_search_and_rerank(query=standalone_query, final_k=6, doc_id=doc_id, regulator=regulator)
    
    context_text = ""
    sources = []
    debug_chunks = []
    
    for idx, chunk in enumerate(retrieved_chunks):
        section = chunk["metadata"].get("section_title", "General")
        text = chunk["text"]
        # Security: Sanitize each retrieved chunk before prompt injection
        text = sanitize_document_text(text, max_chars=8000, source_label=f"chat_chunk_{idx}")
        context_text += f"---\n[Source {idx+1}: {section}]\n{text}\n"
        
        sources.append({
            "section_title": section,
            "snippet": text[:150] + "...",
            "score": chunk.get("mmr_score", chunk.get("rerank_score", 0))
        })
        debug_chunks.append({"idx": idx+1, "section": section, "text_preview": text[:50]})

    # 5. Filter empty context / Prevent Unrelated Outputs (Step 10: Answer Grounding Validation)
    if not retrieved_chunks:
        reply = "I couldn't find relevant information in the document to answer your question."
        append_to_memory(doc_id, "user", message)
        append_to_memory(doc_id, "assistant", reply)
        return {
            "reply": reply,
            "sources": [],
            "grounded": False,
            "grounding_confidence": 0.0,
            "debug": {"query": standalone_query, "chunks_found": 0, "hallucination_risk": "high"},
        }

    # 6. Question Classification & Dynamic Prompts (Steps 7, 8, 11)
    category = classify_question(standalone_query)
    prompt = build_dynamic_prompt(category, chat_history, context_text, standalone_query, safe_message, regulator)

    # 7. Generate Answer
    from services.observability_service import TraceContext, estimate_grounding_quality
    try:
        with TraceContext("chat.generate", {"doc_id": doc_id, "category": category}):
            reply = generate_text(prompt)
    except Exception as e:
        reply = f"Error generating text: {str(e)}"

    quality = estimate_grounding_quality(reply, sources)
    
    # 8. Append to memory
    append_to_memory(doc_id, "user", message)
    append_to_memory(doc_id, "assistant", reply)
    
    grounding_confidence = quality.get("grounding_score", 0.0)
    grounded = quality.get("risk") != "high"

    return {
        "reply": reply,
        "sources": sources,
        "grounded": grounded,
        "grounding_confidence": grounding_confidence,
        "debug": {
            "category": category,
            "standalone_query": standalone_query,
            "chunks_used": debug_chunks,
            "retrieval_count": len(retrieved_chunks),
            "reasoning_steps": [
                f"1. Query classified as '{category}'",
                f"2. Standalone query: {standalone_query}",
                f"3. Retrieved {len(retrieved_chunks)} chunks via hybrid MMR search",
                f"4. Grounding confidence: {round(grounding_confidence * 100)}%",
                f"5. Hallucination risk: {quality.get('risk', 'unknown')}",
                f"6. Validation flags: {', '.join(quality.get('reasons', [])) or 'None'}"
            ],
            "hallucination_risk": quality.get("risk"),
        },
    }
