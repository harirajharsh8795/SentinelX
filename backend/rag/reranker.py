from typing import List, Dict, Any

# Phase 8: Regulatory action words that indicate high-value compliance content
_REGULATORY_BOOST_WORDS = {
    "must", "shall", "required", "mandatory", "ensure", "comply",
    "penalty", "fine", "violation", "non-compliance", "prohibited",
    "within", "deadline", "immediately", "forthwith",
    "audit", "review", "report", "submit", "notify",
}


import math

def compute_bm25_scores(query: str, chunks: List[Dict[str, Any]]) -> List[float]:
    # Tokenize query and documents
    query_terms = [t for t in query.lower().split() if t]
    if not query_terms or not chunks:
        return [0.0] * len(chunks)
        
    doc_terms_list = []
    for c in chunks:
        terms = [t for t in c.get("text", "").lower().split() if t]
        doc_terms_list.append(terms)
        
    N = len(chunks)
    doc_lengths = [len(terms) for terms in doc_terms_list]
    avgdl = sum(doc_lengths) / N if N > 0 else 1.0
    
    # Calculate IDF for each query term
    idf = {}
    for term in query_terms:
        n_q = sum(1 for terms in doc_terms_list if term in terms)
        val = (N - n_q + 0.5) / (n_q + 0.5)
        # Avoid negative IDF
        idf[term] = math.log(max(val, 0.0001) + 1.0)
        
    k1 = 1.5
    b = 0.75
    
    scores = []
    for i, terms in enumerate(doc_terms_list):
        score = 0.0
        doc_len = doc_lengths[i]
        tf_dict = {}
        for term in terms:
            tf_dict[term] = tf_dict.get(term, 0) + 1
            
        for term in query_terms:
            tf = tf_dict.get(term, 0)
            if tf > 0:
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / avgdl))
                score += idf[term] * (numerator / denominator)
        scores.append(score)
        
    max_score = max(scores) if scores else 0.0
    if max_score > 0.0:
        scores = [s / max_score for s in scores]
    return scores

def jaccard_similarity(text1: str, text2: str) -> float:
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = sum(a * a for a in v1) ** 0.5
    norm2 = sum(b * b for b in v2) ** 0.5
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

def chunk_similarity(c1: Dict[str, Any], c2: Dict[str, Any]) -> float:
    v1 = c1.get("embedding")
    v2 = c2.get("embedding")
    if v1 and v2:
        return cosine_similarity(v1, v2)
    return jaccard_similarity(c1.get("text", ""), c2.get("text", ""))

def rerank_chunks(query: str, chunks: List[Dict[str, Any]], top_k: int = 3, lambda_mult: float = 0.7) -> List[Dict[str, Any]]:
    """
    Phase 8: Enhanced Reranking Layer with:
    1. Short fragment filtering (<80 chars)
    2. Regulatory action word boosting
    3. MMR (Maximal Marginal Relevance) for diversity using embedding cosine similarity
    """
    if not chunks:
        return []

    # Phase 8: Filter out short noisy fragments
    chunks = [c for c in chunks if len(c.get("text", "")) >= 80]
    if not chunks:
        return []

    bm25_scores = compute_bm25_scores(query, chunks)
    
    # 1. First, score all candidates for relevance
    for idx, chunk in enumerate(chunks):
        chunk_text = chunk["text"].lower()
        chunk_terms = set(chunk_text.split())
        
        bm25_score = bm25_scores[idx]
            
        score_val = chunk.get("score", 0.0)
        # If retriever already stored true similarity score (detected by 'distance' key presence)
        if "distance" in chunk:
            vector_score = score_val
        else:
            dist = score_val
            # Handle both Cosine and L2 distances dynamically
            if dist < 1.0:
                vector_score = 1.0 - dist
            else:
                vector_score = 1.0 / (1.0 + dist)

        # Phase 8: Regulatory action word boost
        reg_boost = 0.0
        reg_hits = chunk_terms.intersection(_REGULATORY_BOOST_WORDS)
        if reg_hits:
            reg_boost = min(0.15, len(reg_hits) * 0.03)  # Cap at 0.15

        # vector_score + bm25_score combined: 0.7*vector + 0.3*bm25
        chunk["base_relevance"] = (vector_score * 0.7) + (bm25_score * 0.3) + reg_boost

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
                similarities = [chunk_similarity(chunk, sel) for sel in selected]
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
        
    # Apply score threshold 0.25 filter, keeping at least 1 chunk to prevent empty context
    filtered_selected = []
    for i, c in enumerate(selected):
        if c.get("base_relevance", 0.0) >= 0.25 or i == 0:
            filtered_selected.append(c)
            
    return filtered_selected
