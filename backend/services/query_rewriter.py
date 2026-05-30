import json
from typing import List, Dict, Any, Optional
from services.gemini_service import generate_text
from utils.logger import get_logger

logger = get_logger(__name__)

# Domain abbreviation mapping
DOMAIN_ACRONYMS = {
    "v-cip": "V-CIP Video-based Customer Identification Process remote onboarding KYC verification",
    "vcip": "V-CIP Video-based Customer Identification Process remote onboarding KYC verification",
    "cdd": "Customer Due Diligence CDD KYC risk profiling identity verification customer verification",
    "kyc": "Know Your Customer KYC identity verification onboarding due diligence CDD customer due diligence",
    "aml": "Anti-Money Laundering AML transaction monitoring suspicious activity STR CTR FIU-IND",
    "str": "Suspicious Transaction Report STR AML FIU-IND reporting obligation compliance reporting",
    "ctr": "Cash Transaction Report CTR AML FIU-IND threshold reporting cash transaction",
    "fiu": "Financial Intelligence Unit FIU-IND AML STR CTR reporting regulatory authority",
    "fiu-ind": "Financial Intelligence Unit India FIU-IND AML STR reporting penalties regulatory authority",
    "vapt": "Vulnerability Assessment and Penetration Testing VAPT cybersecurity audit security testing vulnerability evaluation",
    "mfa": "Multi-Factor Authentication MFA access control security two-factor authentication",
    "ciso": "Chief Information Security Officer CISO governance cybersecurity accountability leadership board reporting",
    "uapa": "Unlawful Activities Prevention Act UAPA terror financing sanction screening list",
    "tls": "Transport Layer Security TLS encryption data-in-transit HTTPS protocol",
    "ddos": "Distributed Denial of Service DDoS attack mitigation availability business continuity cyber attack",
    "sla": "Service Level Agreement SLA vendor third-party outsourcing performance thresholds",
    "pii": "Personally Identifiable Information PII data privacy protection masking data security",
}

def expand_domain_terms(query: str, regulator: Optional[str] = None, doc_text_has_aml: bool = False) -> str:
    """Expand abbreviations and add regulatory context for short queries to improve recall."""
    q_lower = query.lower().strip()
    expansions = []
    for abbrev, expansion in DOMAIN_ACRONYMS.items():
        if abbrev in ["aml", "str", "ctr", "fiu", "fiu-ind"]:
            if regulator == "SEBI" or (not doc_text_has_aml and abbrev not in q_lower):
                continue
        # Check boundary to avoid sub-word matching (e.g. 'cdd' in 'cdd-checklist')
        if abbrev in q_lower:
            expansions.append(expansion)
            
    result = query
    if expansions:
        # Append up to 2 domain expansions to prevent query bloat
        result = query + " " + " ".join(expansions[:2])
        
    # General query expansion for short user search phrases (<= 3 words)
    words = result.split()
    if len(words) <= 3:
        result = result + " regulatory compliance requirements audit guidelines mandates and directives"
        
    return result

def generate_multi_queries(query: str, chat_history: str = "") -> List[str]:
    """Generates 3 semantically distinct query formulations using the local/global LLM."""
    prompt = f"""You are a regulatory search optimizer for Indian banking compliance.
Your task is to decompose and expand the following user query into exactly 3 different semantic search queries.
Generate queries that target compliance timelines, audit requirements, or penalties related to the topic.

Return ONLY a JSON list of strings, e.g.:
["cyber incident reporting timelines", "RBI security breach disclosure penalties", "incident reporting process for banks"]

--- CONVERSATION HISTORY ---
{chat_history}

--- USER QUERY ---
{query}

JSON Output:"""
    try:
        response = generate_text(prompt).strip()
        # Clean up response markdown code block wrapper if present
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
        if response.endswith("```"):
            response = response.rsplit("\n", 1)[0]
        response = response.strip()
        
        queries = json.loads(response)
        if isinstance(queries, list) and len(queries) > 0:
            return [str(q).strip() for q in queries[:3]]
    except Exception as e:
        logger.warning(f"Failed to generate multi-queries: {e}. Using fallback query formulation.")
    
    # Fallback formulations
    return [
        query,
        f"{query} compliance audit guidelines",
        f"{query} timeline obligations and penalties"
    ]

def generate_hyde_doc(query: str, chat_history: str = "") -> str:
    """Generates a hypothetical document snippet (HyDE) to align embedding retrieval."""
    prompt = f"""You are a regulatory compliance officer.
Write a 2-sentence hypothetical excerpt from an RBI or SEBI circular that perfectly answers the following query.
Do NOT use meta-text or say "This is an excerpt". Write ONLY the hypothetical text itself.

--- CONVERSATION HISTORY ---
{chat_history}

--- USER QUERY ---
{query}

Hypothetical Text:"""
    try:
        hyde_doc = generate_text(prompt).strip()
        if len(hyde_doc) > 50:
            return hyde_doc
    except Exception as e:
        logger.warning(f"Failed to generate HyDE document snippet: {e}.")
    
    # Fallback to query itself
    return f"This directive outlines mandatory requirements, timelines, and penalties regarding {query}."

def rewrite_query_pipeline(query: str, chat_history: str = "") -> Dict[str, Any]:
    """
    Main orchestration pipeline for Query Rewriting:
    1. Expands acronyms
    2. Generates semantic query reformulations (Multi-Query)
    3. Generates hypothetical response (HyDE)
    """
    expanded_base = expand_domain_terms(query)
    alternative_queries = generate_multi_queries(query, chat_history)
    hyde_document = generate_hyde_doc(query, chat_history)
    
    # Combine everything for a rich context matching retrieval plan
    all_searches = list(set([query, expanded_base] + alternative_queries))
    
    return {
        "original_query": query,
        "expanded_query": expanded_base,
        "alternative_queries": alternative_queries,
        "hyde_document": hyde_document,
        "all_search_queries": all_searches
    }
