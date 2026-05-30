import re
from typing import List, Optional, Dict, Any, Union
from rag.retriever import get_collection, search_similar
from utils.logger import get_logger

logger = get_logger(__name__)

def keyword_search(
    query: str,
    top_k: int = 5,
    doc_id: Optional[Union[str, List[str]]] = None,
    regulator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Step 3: Exact Keyword Search Simulation
    Chroma doesn't natively do BM25 without extra integrations, so we pull top N via semantic 
    and do a broader keyword regex fallback or we just use Semantic as base and let Reranker handle the BM25 aspect.
    
    For True Hybrid:
    We'll do a vector search but request a wider recall (e.g. top_k = 10 or 15).
    Then we apply our reranker to act as the second phase of hybrid search.
    """
    return search_similar(query, top_k=top_k, doc_id=doc_id, regulator=regulator)

def hybrid_search_and_rerank(
    query: str,
    final_k: int = 3,
    doc_id: Optional[Union[str, List[str]]] = None,
    regulator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Combines Query Rewriting (Multi-Query + HyDE), Vector Search, Deduplication, and Reranking:
    1. Expand original query into multiple semantic intents and a hypothetical answer (HyDE).
    2. Query ChromaDB for all expanded targets to build a broad candidate pool.
    3. Deduplicate candidates to prevent redundancy.
    4. Rerank candidates using keyword match, regulatory boost, and MMR diversity.
    """
    from services.query_rewriter import expand_domain_terms
    from rag.reranker import rerank_chunks
    
    # Resolve doc_text_has_aml dynamically
    doc_text_has_aml = False
    if doc_id and not isinstance(doc_id, list):
        try:
            from rag.retriever import get_collection
            collection = get_collection(doc_id)
            res = collection.get(where={"doc_id": doc_id}, limit=50)
            for doc_text in res.get("documents", []):
                text_lower = doc_text.lower()
                if "aml" in text_lower or "money laundering" in text_lower or "fiu-ind" in text_lower or "suspicious transaction" in text_lower:
                    doc_text_has_aml = True
                    break
        except Exception:
            pass

    # 1. Lightweight domain-aware expansion (NO LLM calls — fast)
    expanded_query = expand_domain_terms(query, regulator=regulator, doc_text_has_aml=doc_text_has_aml)
 
    # 2. Gather candidates from original + expanded queries
    candidates = []
    seen_ids = set()
    
    # Query with both original and domain-expanded versions
    query_targets = list(set([query, expanded_query]))
    
    for q in query_targets:
        results = search_similar(q, top_k=12, doc_id=doc_id, regulator=regulator)
        for r in results:
            meta = r.get("metadata", {})
            # Construct a unique key for deduplication
            chunk_id = f"{meta.get('doc_id')}-{meta.get('chunk_index', 0)}"
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                candidates.append(r)
                
    # 3. Rerank the gathered candidates using the original query
    reranked = rerank_chunks(query, candidates, top_k=final_k)
    
    return reranked
