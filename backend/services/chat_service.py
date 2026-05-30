import os
import asyncio
from typing import Dict, List, Any
from rag.hybrid_search import hybrid_search_and_rerank
from services.gemini_service import generate_text, generate_text_async
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

async def rewrite_query(original_query: str, chat_history: str, regulator: str = "RBI", doc_text_has_aml: bool = False) -> str:
    """
    Semantic Query Rewriting Engine (Phase 1):
    1. Resolves pronouns using conversation history.
    2. Expands domain-specific terminology (V-CIP, CDD, FIU-IND, etc.).
    3. Adds compliance intent keywords (timelines, penalties, audit obligations).
    """
    # Even without history, expand domain terms for better retrieval
    expanded = _expand_domain_terms(original_query, regulator=regulator, doc_text_has_aml=doc_text_has_aml)

    if "No previous conversation" in chat_history:
        return expanded

    abbrev_rules = "V-CIP → Video-based Customer Identification Process, CDD → Customer Due Diligence, VAPT → Vulnerability Assessment and Penetration Testing, MFA → Multi-Factor Authentication, CISO → Chief Information Security Officer."
    if regulator != "SEBI" and doc_text_has_aml:
        abbrev_rules += " STR → Suspicious Transaction Report, CTR → Cash Transaction Report, FIU-IND → Financial Intelligence Unit India."

    negative_rules = ""
    if regulator == "SEBI" or not doc_text_has_aml:
        negative_rules = "5. Do NOT expand or inject AML/STR/FIU-IND or money laundering terms for this query."

    prompt = f"""You are a regulatory compliance search query optimizer for Indian banking.

TASK: Rewrite the user's query into a rich, standalone search query.

RULES:
1. Resolve all pronouns ("it", "this", "that") using conversation history.
2. Expand abbreviations: {abbrev_rules}
3. Add compliance intent keywords where relevant (e.g., timelines, deadlines, penalties, audit requirements, reporting obligations).
4. Keep the query under 120 words. Return ONLY the rewritten query text, nothing else.
{negative_rules}

--- PAST CONVERSATION HISTORY ---
{chat_history}

--- USER QUERY ---
{original_query}

Rewritten Query:"""
    try:
        rewritten = await generate_text_async(prompt, timeout=45)
        rewritten = rewritten.strip()
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


def _expand_domain_terms(query: str, regulator: str = "RBI", doc_text_has_aml: bool = False) -> str:
    """Expand abbreviated regulatory terms into rich search phrases."""
    import re
    q_lower = query.lower()
    expansions = []
    for abbrev, expansion in _DOMAIN_EXPANSIONS.items():
        if abbrev in ["aml", "str", "ctr", "fiu", "fiu-ind"]:
            has_abbrev_in_query = bool(re.search(r'\b' + re.escape(abbrev) + r'\b', q_lower))
            if regulator == "SEBI" or (not doc_text_has_aml and not has_abbrev_in_query):
                continue
        # Use exact word boundary matching to avoid sub-word matching (e.g., matching 'str' in 'restrictions')
        if re.search(r'\b' + re.escape(abbrev) + r'\b', q_lower):
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

def classify_question(query: str, doc_text_has_aml: bool = False) -> str:
    """
    Question Classification:
    Categorizes the query into one of 9 distinct intents for targeted compliance prompting.
    """
    q = query.lower().strip()
    if any(w in q for w in ["governance", "board", "director", "management", "committee", "ciso", "roles", "responsibilities", "registration", "compliance"]):
        return "governance"
    if any(w in q for w in ["vendor", "outsourcing", "third-party", "supplier", "partner", "procurement", "sla"]):
        return "vendor_risk"
    if any(w in q for w in ["deadline", "timeline", "when", "days", "months", "date", "schedule", "period"]):
        return "timelines"
    if any(w in q for w in ["penalty", "punishment", "fine", "violation", "non-compliance", "lawsuit", "prosecution", "sanction"]):
        return "penalties"
    if any(w in q for w in ["aml", "anti-money laundering", "money laundering", "transaction monitoring", "terrorist financing"]):
        if doc_text_has_aml:
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

STRICT RULES — NO EXCEPTIONS:

1. ONLY use information explicitly 
   written in the document context.

2. NEVER use these phrases:
   - "fines and penalties"
   - "reputational damage"  
   - "best practices"
   - "ensure compliance"
   - "it is recommended"
   - "regulatory penalties"
   Unless they appear WORD FOR WORD 
   in the retrieved chunks.

3. If a fact is NOT in chunks:
   Write exactly: 
   "[Not found in document]"
   after that specific claim.

4. For EVERY claim, mentally ask:
   "Which exact chunk supports this?"
   If no chunk → do NOT include it.

5. Departments like "Legal Affairs 
   Division", "Cross-border Operations"
   — ONLY mention if document 
   explicitly names them.
   Otherwise write: 
   "[Department not specified 
   in document]"

6. Source citations MUST include:
   - Exact chapter/section number
   - Exact regulation number
   - Exact clause if available
   NEVER generic "RBI (2023)" only.

For EVERY claim you make, 
cite the source like this:

[Chapter X, Section Y.Z] or
[Regulation X(Y)] or  
[Clause X(Y)(Z)]

Example:
'REs must comply by Oct 1, 2023
[Chapter II, Section II(i)]'

NEVER write generic citations like
'RBI (2023)' alone.
If you cannot find exact section,
write '[Section not identified]'

NO-EVIDENCE FALLBACK: If the context does NOT contain direct evidence or information to answer the question, you MUST format your reply EXACTLY like this:
## Information Not Found
The uploaded document does not explicitly specify [topic].
**What the document does cover:**
- [list what IS in the document context]
**Suggestion:** Check [specific section/references] of the circular for related information.

NUMERICAL REASONING: When user provides specific numbers (clients, amounts, dates), apply them directly to the regulatory tables found in context.
   Example:
   User says '850 clients'
   Document says:
   '301-1000 clients = ₹5 lakh'
   You MUST calculate:
   850 falls in 301-1000 bracket
   Therefore deposit = ₹5 lakh
   Always show your calculation step by step.

COMPLIANCE OBLIGATION TABLES: When asked about compliance obligations, ALWAYS structure response as:
| Obligation | Regulation | Deadline | Department | Risk if Delayed |
|-----------|-----------|---------|-----------|----------------|
| [specific] | Reg. X | [date] | [dept] | [consequence] |
Extract this information ONLY from the document context. Do not guess deadlines or departments.

CITE sources using the exact source number, e.g., "(Source 1)".
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

# Hinglish/short query expansion — maps common Hinglish commands to English equivalents
_HINGLISH_EXPANSIONS = {
    "risk btao": "What are the main risks mentioned in this document?",
    "risks btao": "What are the main risks mentioned in this document?",
    "risk batao": "What are the main risks mentioned in this document?",
    "summary do": "Provide a detailed summary of this document.",
    "summarize karo": "Provide a detailed summary of this document.",
    "kya hai": "What is this document about?",
    "ye kya hai": "What is this document about?",
    "penalty btao": "What are the penalties mentioned in this document?",
    "penalties btao": "What are the penalties mentioned in this document?",
    "deadline btao": "What are the deadlines and timelines in this document?",
    "audit btao": "What are the audit requirements in this document?",
    "compliance btao": "What are the compliance requirements in this document?",
    "kyc btao": "What are the KYC requirements mentioned in this document?",
    "cyber btao": "What are the cybersecurity requirements in this document?",
}

def expand_hinglish_query(message: str) -> str:
    """Expand short Hinglish queries into full English search queries."""
    msg_lower = message.strip().lower()
    # Direct match
    if msg_lower in _HINGLISH_EXPANSIONS:
        return _HINGLISH_EXPANSIONS[msg_lower]
    # Partial match for very short queries (< 4 words)
    words = msg_lower.split()
    if len(words) <= 3:
        for pattern, expansion in _HINGLISH_EXPANSIONS.items():
            pattern_words = pattern.split()
            if all(pw in words for pw in pattern_words):
                return expansion
    return message


def doc_has_aml_content(doc_id: str) -> bool:
    if not doc_id:
        return False
    try:
        from rag.retriever import get_collection
        collection = get_collection(doc_id)
        res = collection.get(where={"doc_id": doc_id}, limit=50)
        for doc_text in res.get("documents", []):
            text_lower = doc_text.lower()
            if any(w in text_lower for w in ["aml", "money laundering", "fiu-ind", "suspicious transaction"]):
                return True
    except Exception:
        pass
    return False


async def chat_with_document(doc_id: str, message: str) -> Dict[str, Any]:
    """
    Combines conversational memory, Query Rewriting, Question Classification, 
    and Hybrid MMR RAG Retrieval to answer contextually.
    """
    # 0. Expand Hinglish/short queries to English equivalents
    expanded_message = expand_hinglish_query(message)

    # 1. Resolve regulator constraint
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    regulator = doc.regulator if (doc and doc.regulator) else "RBI"
    db.close()

    # Determine if document text has AML keywords dynamically
    doc_text_has_aml = doc_has_aml_content(doc_id)

    # 2. Get past chat history (Step 13: Chat Memory)
    chat_history = get_chat_history(doc_id)
    
    # 3. Semantic Query Rewriting (Step 6)
    standalone_query = await rewrite_query(expanded_message, chat_history, regulator=regulator, doc_text_has_aml=doc_text_has_aml)

    # Security: Sanitize user message before it enters any prompt
    safe_message = sanitize_user_query(message)
    
    # 4. Retrieve chunks with MMR enabled + strict regulator isolation (Phase 3)
    retrieved_chunks = await asyncio.to_thread(hybrid_search_and_rerank, query=standalone_query, final_k=8, doc_id=doc_id, regulator=regulator)
    
    context_text = ""
    sources = []
    debug_chunks = []
    
    import re
    for idx, chunk in enumerate(retrieved_chunks):
        section = chunk["metadata"].get("section_title", "General")
        text = chunk["text"]
        # Replace Devanagari text with [Hindi text] in the snippet for UI display
        snippet = text[:150]
        snippet = snippet.replace("भारतीय रज़वर् ब क", "[Hindi text]")
        snippet = re.sub(r'[\u0900-\u097F]+', '[Hindi text]', snippet)
        snippet = re.sub(r'(\[Hindi text\]\s*)+', '[Hindi text]', snippet)
        
        # Security: Sanitize each retrieved chunk before prompt injection
        text = sanitize_document_text(text, max_chars=8000, source_label=f"chat_chunk_{idx}")
        context_text += f"---\n[Source {idx+1}: {section}]\n{text}\n"
        
        sources.append({
            "section_title": section,
            "snippet": snippet.strip() + "...",
            "score": chunk.get("mmr_score", chunk.get("rerank_score", 0))
        })
        debug_chunks.append({"idx": idx+1, "section": section, "text_preview": text[:50]})

    # 5. Graceful No-evidence Penalties Fallback
    is_penalty_query = "penalt" in message.lower()
    if is_penalty_query:
        has_penalty_evidence = False
        for chunk in retrieved_chunks:
            if "penalt" in chunk["text"].lower():
                has_penalty_evidence = True
                break
        if not has_penalty_evidence:
            reply = """## Penalty Information Not Found

This document does not explicitly specify penalties for non-compliance.

**What this document does specify:**
- Compliance timelines
- Governance obligations  
- Outsourcing requirements

For penalty clauses, refer to:
The parent RBI Act or specific enforcement circulars."""
            append_to_memory(doc_id, "user", message)
            append_to_memory(doc_id, "assistant", reply)
            return {
                "reply": reply,
                "sources": sources,
                "grounded": True,
                "grounding_confidence": 1.0,
                "debug": {
                    "category": "penalties",
                    "standalone_query": standalone_query,
                    "chunks_used": debug_chunks,
                    "retrieval_count": len(retrieved_chunks),
                    "reasoning_steps": [
                        "1. Query classified as penalties",
                        "2. No evidence of penalties found in retrieved chunks",
                        "3. Returned graceful Penalty Information Not Found response"
                    ],
                    "hallucination_risk": "low"
                }
            }

    # 6. Filter empty context / Prevent Unrelated Outputs (Step 10: Answer Grounding Validation)
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

    # 7. Question Classification & Dynamic Prompts (Steps 7, 8, 11)
    category = classify_question(standalone_query, doc_text_has_aml=doc_text_has_aml)
    prompt = build_dynamic_prompt(category, chat_history, context_text, standalone_query, safe_message, regulator)

    # 8. Generate Answer with 45s hard timeout
    from services.observability_service import TraceContext, estimate_grounding_quality
    try:
        with TraceContext("chat.generate", {"doc_id": doc_id, "category": category}):
            reply = await generate_text_async(prompt, timeout=45.0)
    except Exception as e:
        logger.warning(f"Failed to generate text or timed out after 45s: {e}. Generating partial analysis fallback.")
        summary_bullets = []
        for idx, chunk in enumerate(retrieved_chunks[:3]):
            section = chunk["metadata"].get("section_title", "General")
            snippet = chunk["text"][:200].strip()
            snippet = re.sub(r'\s+', ' ', snippet)
            snippet = re.sub(r'[\u0900-\u097F]+', '[Hindi text]', snippet)
            snippet = re.sub(r'(\[Hindi text\]\s*)+', '[Hindi text]', snippet)
            summary_bullets.append(f"- **{section}**: {snippet}...")
        summary_text = "\n".join(summary_bullets)
        reply = f"""## Partial Analysis
Based on retrieved context:

{summary_text}

⚠️ Full analysis timed out. Try a more specific query."""

    quality = estimate_grounding_quality(reply, sources)
    reply = quality.get("validated_reply", reply)
    
    # 9. Append to memory
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
