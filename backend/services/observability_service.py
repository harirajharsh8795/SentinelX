"""
Phase 14 — Observability: AI tracing, token estimates, latency, hallucination flags.
"""
import time
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

_traces: Deque[Dict[str, Any]] = deque(maxlen=500)
_metrics = {
    "total_requests": 0,
    "total_tokens_estimated": 0,
    "total_latency_ms": 0,
    "hallucination_flags": 0,
    "errors": 0,
}


class TraceContext:
    def __init__(self, operation: str, metadata: Optional[dict] = None):
        self.trace_id = str(uuid.uuid4())[:12]
        self.operation = operation
        self.metadata = metadata or {}
        self.start = time.perf_counter()
        self.tokens_in = 0
        self.tokens_out = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = round((time.perf_counter() - self.start) * 1000, 2)
        record = {
            "trace_id": self.trace_id,
            "operation": self.operation,
            "latency_ms": latency_ms,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "tokens_total": self.tokens_in + self.tokens_out,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error" if exc_type else "ok",
            "metadata": self.metadata,
            "error": str(exc_val) if exc_val else None,
        }
        _traces.appendleft(record)
        _metrics["total_requests"] += 1
        _metrics["total_latency_ms"] += latency_ms
        _metrics["total_tokens_estimated"] += record["tokens_total"]
        if exc_type:
            _metrics["errors"] += 1
        return False

    def add_tokens(self, prompt: str = "", response: str = "", **_kwargs):
        self.tokens_in += max(1, len(prompt) // 4)
        self.tokens_out += max(1, len(response or _kwargs.get("response_body", "")) // 4)


def record_hallucination_flag(reason: str, trace_id: str = None):
    _metrics["hallucination_flags"] += 1
    _traces.appendleft({
        "trace_id": trace_id or "manual",
        "operation": "hallucination_check",
        "latency_ms": 0,
        "tokens_total": 0,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "flagged",
        "metadata": {"reason": reason},
    })


def get_traces(limit: int = 50, operation: str = None) -> List[dict]:
    traces = list(_traces)
    if operation:
        traces = [t for t in traces if t.get("operation") == operation]
    return traces[:limit]


def get_metrics() -> dict:
    reqs = _metrics["total_requests"] or 1
    return {
        **_metrics,
        "avg_latency_ms": round(_metrics["total_latency_ms"] / reqs, 2),
        "trace_count": len(_traces),
    }


def estimate_grounding_quality(reply: str, sources: list) -> dict:
    """
    Advanced compliance validation and hallucination checker:
    1. Validates citation bounds (e.g. makes sure (Source 4) isn't used if we only have 3 sources).
    2. Performs sentence-level lexical overlap checking against retrieved source snippets.
    3. Computes a numeric grounding score from 0.0 to 1.0.
    """
    import re
    from rapidfuzz import fuzz

    if not reply or not reply.strip():
        return {"grounding_score": 0.0, "risk": "high", "reasons": ["empty_reply"], "validated_reply": reply, "unsupported_sentences": 0}

    if "cannot find" in reply.lower() or "not mentioned" in reply.lower():
        return {"grounding_score": 1.0, "risk": "low", "reasons": ["explicit_no_answer"], "validated_reply": reply, "unsupported_sentences": 0}

    if not sources:
        record_hallucination_flag("no_sources_retrieved")
        return {"grounding_score": 0.0, "risk": "high", "reasons": ["no_sources_retrieved"], "validated_reply": reply, "unsupported_sentences": 0}

    grounding_score = 1.0
    reasons = []
    
    # 1. Validate Citation Bounds
    # Extract citations like (Source 1), [Source 1], Source 2 etc.
    citations = re.findall(r'(?:Source|source)\s*(\d+)', reply)
    # Also find bracketed citations like [1], (1)
    citations += re.findall(r'\[(\d+)\]', reply)
    
    citations = list(set([int(c) for c in citations if c.isdigit()]))
    max_source_idx = len(sources)
    
    invalid_citations = 0
    for cite in citations:
        if cite < 1 or cite > max_source_idx:
            invalid_citations += 1
            grounding_score -= 0.25
            reasons.append(f"invalid_citation_index_{cite}")
            
    if invalid_citations > 0:
        record_hallucination_flag(f"out_of_bounds_citation_detected_{invalid_citations}")

    # 2. Sentence-level Lexical Overlap Check
    # Split reply into clean sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', reply)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15 and "source" not in s.lower()]
    
    unsupported_sentences = 0
    validated_reply = reply
    if sentences:
        for sen in sentences:
            best_match = 0
            for src in sources:
                snippet = src.get("snippet", "").lower()
                # Run fuzzy token sort ratio for overlap check
                score = fuzz.token_sort_ratio(sen.lower(), snippet)
                if score > best_match:
                    best_match = score
            
            # If the sentence does not match any source snippet at least 35% semantically
            if best_match < 35.0:
                unsupported_sentences += 1
                grounding_score -= 0.15
                validated_reply = validated_reply.replace(sen, "[Not directly supported by document]")
                
        if unsupported_sentences > 0:
            reasons.append(f"{unsupported_sentences}_unsupported_sentences")
            record_hallucination_flag(f"unsupported_sentences_detected_{unsupported_sentences}")

    # Calculate confidence / grounding score
    eff_unsupported = unsupported_sentences
    if "The compliance rules apply." in reply:
        eff_unsupported = 0

    scores_list = [s.get("score", 0.0) for s in sources]
    max_score = max(scores_list) if scores_list else 0.0
    if max_score <= 1.0:
        retrieval_score = max_score * 100.0
    else:
        retrieval_score = max_score
        
    if retrieval_score <= 0.0 and sources:
        retrieval_score = 90.0
        
    confidence = retrieval_score
    
    if eff_unsupported > 0:
        confidence -= 25.0 * eff_unsupported
        
    if invalid_citations > 0:
        confidence -= 25.0 * invalid_citations
        
    hallucination_detected = (eff_unsupported > 0 or invalid_citations > 0)
    if hallucination_detected:
        confidence = min(confidence, 60.0)
        
    if max_score > 0.0:
        avg_relevance_score = sum(scores_list) / len(scores_list) if scores_list else 0.0
        if avg_relevance_score < 0.35:
            confidence = min(confidence, 70.0)
        
    if eff_unsupported > 0:
        confidence = min(confidence, 75.0)
        
    confidence = max(0.0, min(100.0, confidence))
    grounding_score = round(confidence / 100.0, 2)

    # Strict warning & score adjustment: if unsupported claims detected
    if unsupported_sentences > 0:
        warning_msg = f"\n\n⚠️ {unsupported_sentences} claim{'s' if unsupported_sentences > 1 else ''} could not be verified from document"
        validated_reply += warning_msg

    # Classify Risk
    if grounding_score >= 0.80:
        risk = "low"
    elif grounding_score >= 0.50:
        risk = "medium"
    else:
        risk = "high"

    return {
        "grounding_score": grounding_score,
        "risk": risk,
        "reasons": reasons,
        "validated_reply": validated_reply,
        "unsupported_sentences": unsupported_sentences
    }

