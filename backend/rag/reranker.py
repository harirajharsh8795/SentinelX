from typing import List, Dict, Any

# Phase 8: Regulatory action words that indicate high-value compliance content
_REGULATORY_BOOST_WORDS = {
    "must", "shall", "required", "mandatory", "ensure", "comply",
    "penalty", "fine", "violation", "non-compliance", "prohibited",
    "within", "deadline", "immediately", "forthwith",
    "audit", "review", "report", "submit", "notify",
}


def jaccard_similarity(text1: str, text2: str) -> float:
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def rerank_chunks(query: str, chunks: List[Dict[str, Any]], top_k: int = 3, lambda_mult: float = 0.7) -> List[Dict[str, Any]]:
    """
    Phase 8: Enhanced Reranking Layer with:
    1. Short fragment filtering (<80 chars)
    2. Regulatory action word boosting
    3. MMR (Maximal Marginal Relevance) for diversity
    """
    if not chunks:
        return []

    # Phase 8: Filter out short noisy fragments
    chunks = [c for c in chunks if len(c.get("text", "")) >= 80]
    if not chunks:
        return []

    query_terms = set(query.lower().split())
    
    # 1. First, score all candidates for relevance
    for chunk in chunks:
        chunk_text = chunk["text"].lower()
        chunk_terms = set(chunk_text.split())
        
        # Relevance: Combine vector score + exact match Jaccard
        if query_terms:
            intersection = len(query_terms.intersection(chunk_terms))
            union = len(query_terms.union(chunk_terms))
            jaccard_rel = intersection / union if union > 0 else 0
        else:
            jaccard_rel = 0
            
        vector_score = 1.0 / (1.0 + chunk.get("score", 0.0))

        # Phase 8: Regulatory action word boost
        reg_boost = 0.0
        reg_hits = chunk_terms.intersection(_REGULATORY_BOOST_WORDS)
        if reg_hits:
            reg_boost = min(0.15, len(reg_hits) * 0.03)  # Cap at 0.15

        chunk["base_relevance"] = (vector_score * 0.6) + (jaccard_rel * 0.25) + reg_boost

    # 2. Apply MMR (Maximal Marginal Relevance)
    # Select the first chunk directly based on highest relevance
    candidates = sorted(chunks, key=lambda x: x["base_relevance"], reverse=True)
    selected = []
    
    while len(selected) < top_k and candidates:
        best_score = -float('inf')
        best_chunk = None
        best_idx = -1
        
        for i, chunk in enumerate(candidates):
            # Calculate max similarity to ALREADY SELECTED chunks (Redundancy)
            if not selected:
                redundancy_penalty = 0.0
            else:
                similarities = [jaccard_similarity(chunk["text"], sel["text"]) for sel in selected]
                redundancy_penalty = max(similarities)
                
            # MMR Equation: score = Lambda * Relevance - (1 - Lambda) * Redundancy
            mmr_score = (lambda_mult * chunk["base_relevance"]) - ((1 - lambda_mult) * redundancy_penalty)
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_chunk = chunk
                best_idx = i
                
        # Move best chunk to selected
        best_chunk["rerank_score"] = best_chunk["base_relevance"]  # store original relevance for UI
        best_chunk["mmr_score"] = best_score
        selected.append(best_chunk)
        candidates.pop(best_idx)
        
    return selected
