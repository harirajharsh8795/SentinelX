import re
from typing import List, Optional, Dict, Any, Union
from collections import defaultdict
from rag.retriever import get_collection, search_similar
from utils.logger import get_logger

logger = get_logger(__name__)

def is_broad_query(query: str) -> bool:
    """Analyze query to check if it's broad or document-wide."""
    q = query.lower().strip()
    broad_words = {
        "summary", "summarize", "outline", "list all", "all obligations", 
        "every", "deadlines", "timelines", "overview", "entire document", 
        "whole document", "audit requirements", "responsibilities", "governance structure",
        "key obligations", "risk mitigation", "penalties"
    }
    words = q.split()
    return any(w in q for w in broad_words) or len(words) <= 2

def keyword_search(
    query: str,
    top_k: int = 5,
    doc_id: Optional[Union[str, List[str]]] = None,
    regulator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return search_similar(query, top_k=top_k, doc_id=doc_id, regulator=regulator)
def hybrid_search_and_rerank(
    query: str,
    final_k: int = 8,
    doc_id: Optional[Union[str, List[str]]] = None,
    regulator: Optional[str] = None,
    full_coverage_mode: bool = False,
    diagnostic_info: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Advanced compliance RAG retrieval pipeline with:
    1. Adaptive Top-K selection based on query intent.
    2. Stratified Full Document Coverage Mode for broad queries.
    3. Section-level context expansion.
    4. Adjacent neighbor chunk expansion to preserve boundaries.
    5. Detailed retrieval diagnostics.
    """
    from services.query_rewriter import expand_domain_terms
    from rag.reranker import rerank_chunks
    
    # Enforce mandatory doc_id filtering
    if not doc_id:
        logger.warning("hybrid_search_and_rerank invoked without doc_id! Strict document isolation enforces that doc_id is mandatory.")
        return []
    
    # 0. Check for broad queries
    broad_query = is_broad_query(query)
    is_full_coverage = full_coverage_mode or (broad_query and not isinstance(doc_id, list))
    
    if diagnostic_info is not None:
        diagnostic_info["broad_query_detected"] = broad_query
        diagnostic_info["full_coverage_mode_active"] = is_full_coverage

    # Mode 1: Full Document Coverage Mode (Stratified sampling of the entire document)
    if is_full_coverage and doc_id and not isinstance(doc_id, list):
        try:
            collection = get_collection(doc_id)
            res = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
            docs = res.get("documents", []) or []
            metas = res.get("metadatas", []) or []
            
            candidates = []
            for doc_text, m in zip(docs, metas):
                # Strict Document Isolation Filter (Contamination Check)
                cand_id = m.get("doc_id") or m.get("document_id")
                if cand_id != doc_id:
                    logger.warning(f"SECURITY ALERT: Cross-document contamination detected in full coverage! Discarded chunk from {cand_id} when querying {doc_id}.")
                    continue
                candidates.append({
                    "text": doc_text,
                    "metadata": m,
                    "score": 0.0,
                    "base_relevance": 1.0
                })
            
            # Sort chronologically by chunk_index
            candidates.sort(key=lambda x: x["metadata"].get("chunk_index", 0))
            
            # Sample chunks to fit within reasonable context budget (cap at 40 chunks, ~10-15k tokens)
            max_coverage_chunks = 40
            if len(candidates) > max_coverage_chunks:
                step = len(candidates) / max_coverage_chunks
                sampled = []
                for i in range(max_coverage_chunks):
                    idx = int(i * step)
                    if idx < len(candidates):
                        sampled.append(candidates[idx])
                candidates = sampled
                
            if diagnostic_info is not None:
                diagnostic_info["original_candidate_count"] = len(docs)
                diagnostic_info["expanded_section_chunks"] = 0
                diagnostic_info["expanded_neighbor_chunks"] = 0
                diagnostic_info["total_retrieved"] = len(candidates)
                
            return candidates
        except Exception as e:
            logger.error(f"Error in full document coverage path: {e}. Falling back to standard search.")

    # Resolve doc_text_has_aml dynamically
    doc_text_has_aml = False
    if doc_id and not isinstance(doc_id, list):
        try:
            collection = get_collection(doc_id)
            res = collection.get(where={"doc_id": doc_id}, limit=50)
            for doc_text in res.get("documents", []):
                text_lower = doc_text.lower()
                if "aml" in text_lower or "money laundering" in text_lower or "fiu-ind" in text_lower or "suspicious transaction" in text_lower:
                    doc_text_has_aml = True
                    break
        except Exception:
            pass

    # 1. Domain-aware term expansion
    expanded_query = expand_domain_terms(query, regulator=regulator, doc_text_has_aml=doc_text_has_aml)

    # 2. Adaptive Top-K setting
    if broad_query:
        candidate_k = 25
        target_final_k = 15
    else:
        candidate_k = 12
        target_final_k = final_k

    if diagnostic_info is not None:
        diagnostic_info["adaptive_top_k"] = {
            "candidate_k": candidate_k,
            "target_final_k": target_final_k
        }

    # Fetch chat history to pass to HyDE and Multi-Query
    chat_history = "No previous conversation."
    if doc_id and isinstance(doc_id, str):
        try:
            from database.database import get_db_context
            from database.models import ChatMessage
            with get_db_context() as db:
                history = db.query(ChatMessage).filter(ChatMessage.session_id == doc_id).order_by(ChatMessage.created_at.desc()).limit(6).all()
                if history:
                    history = history[::-1]
                    chat_history = "\n".join(f"{'User' if msg.role == 'user' else 'AI'}: {msg.content}" for msg in history)
        except Exception as e:
            logger.warning(f"Error fetching chat history in hybrid_search: {e}")

    # Generate HyDE and Multi-Queries
    from services.query_rewriter import generate_hyde_doc, generate_multi_queries
    hyde_document = generate_hyde_doc(query, chat_history)
    alternative_queries = generate_multi_queries(query, chat_history)

    # 3. Gather candidates
    candidates = []
    seen_ids = set()
    query_targets = [query, expanded_query]
    if hyde_document:
        query_targets.append(hyde_document)
    if alternative_queries:
        query_targets.extend(alternative_queries)

    # Deduplicate query targets
    deduped_targets = []
    for q in query_targets:
        if q and q not in deduped_targets:
            deduped_targets.append(q)
    query_targets = deduped_targets

    if diagnostic_info is not None:
        diagnostic_info["query_targets"] = query_targets
        diagnostic_info["hyde_document"] = hyde_document
        diagnostic_info["multi_queries"] = alternative_queries

    for q in query_targets:
        results = search_similar(q, top_k=candidate_k, doc_id=doc_id, regulator=regulator)
        for r in results:
            meta = r.get("metadata", {})
            chunk_id = f"{meta.get('doc_id')}-{meta.get('chunk_index', 0)}"
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                candidates.append(r)

    if diagnostic_info is not None:
        diagnostic_info["original_candidate_count"] = len(candidates)

    # 4. Rerank candidates using original query
    selected_chunks = rerank_chunks(query, candidates, top_k=target_final_k)
    
    # Track selected IDs for expansion deduplication
    seen_selected_ids = {
        f"{c.get('metadata', {}).get('doc_id')}-{c.get('metadata', {}).get('chunk_index')}" 
        for c in selected_chunks
    }

    # 5. Neighbor Chunk Expansion (fetch i-1 and i+1 neighbors for top 4 relevance chunks)
    expanded_neighbor_chunks = []
    neighbor_ids_to_fetch = []
    for chunk in selected_chunks[:4]:
        m = chunk.get("metadata", {})
        idx = m.get("chunk_index")
        doc_id_val = m.get("doc_id")
        if idx is not None and doc_id_val:
            # Check left neighbor
            if idx > 0:
                left_id = f"{doc_id_val}-{idx - 1}"
                if left_id not in seen_selected_ids:
                    neighbor_ids_to_fetch.append((left_id, doc_id_val))
                    seen_selected_ids.add(left_id)
            # Check right neighbor
            right_id = f"{doc_id_val}-{idx + 1}"
            if right_id not in seen_selected_ids:
                neighbor_ids_to_fetch.append((right_id, doc_id_val))
                seen_selected_ids.add(right_id)

    # Group by collection and batch fetch to avoid round-trips
    if neighbor_ids_to_fetch:
        grouped_neighbors = defaultdict(list)
        for nid, d_val in neighbor_ids_to_fetch:
            grouped_neighbors[d_val].append(nid)
            
        for d_val, ids_list in grouped_neighbors.items():
            try:
                coll = get_collection(d_val)
                res = coll.get(ids=ids_list, include=["documents", "metadatas", "embeddings"])
                docs = res.get("documents", []) or []
                metas = res.get("metadatas", []) or []
                embs = res.get("embeddings", []) if res.get("embeddings") else [None] * len(docs)
                for doc_text, m, emb in zip(docs, metas, embs):
                    expanded_neighbor_chunks.append({
                        "text": doc_text,
                        "metadata": m,
                        "score": 0.0,
                        "distance": 1.0,
                        "embedding": emb,
                        "base_relevance": 0.35,
                        "is_neighbor_expansion": True
                    })
            except Exception as e:
                logger.error(f"Error fetching expanded neighbors for {d_val}: {e}")

    # 6. Section Expansion Retrieval (Fetch additional context for top 2 active sections)
    expanded_section_chunks = []
    sections_to_expand = defaultdict(list)
    for chunk in selected_chunks[:2]:
        m = chunk.get("metadata", {})
        section = m.get("section_title")
        d_val = m.get("doc_id")
        if section and section != "General" and d_val:
            if section not in sections_to_expand[d_val]:
                sections_to_expand[d_val].append(section)

    for d_val, sections in sections_to_expand.items():
        for sec in sections:
            try:
                coll = get_collection(d_val)
                res = coll.get(
                    where={"$and": [{"doc_id": d_val}, {"section_title": sec}]},
                    include=["documents", "metadatas", "embeddings"]
                )
                docs = res.get("documents", []) or []
                metas = res.get("metadatas", []) or []
                embs = res.get("embeddings", []) if res.get("embeddings") else [None] * len(docs)
                
                added_count = 0
                for doc_text, m, emb in zip(docs, metas, embs):
                    idx = m.get("chunk_index")
                    chunk_id = f"{d_val}-{idx}"
                    if chunk_id not in seen_selected_ids:
                        expanded_section_chunks.append({
                            "text": doc_text,
                            "metadata": m,
                            "score": 0.0,
                            "distance": 1.0,
                            "embedding": emb,
                            "base_relevance": 0.35,
                            "is_section_expansion": True
                        })
                        seen_selected_ids.add(chunk_id)
                        added_count += 1
                        if added_count >= 3:  # Cap expansion per section
                            break
            except Exception as e:
                logger.error(f"Error expanding section '{sec}' for {d_val}: {e}")

    # 7. Merge and sort chronologically for coherent reading
    combined = selected_chunks + expanded_neighbor_chunks + expanded_section_chunks
    combined.sort(key=lambda x: (x.get("metadata", {}).get("doc_id", ""), x.get("metadata", {}).get("chunk_index", 0)))

    # Strict Document Isolation Filter (Contamination Check)
    filtered_combined = []
    for c in combined:
        cand_id = c.get("metadata", {}).get("doc_id") or c.get("metadata", {}).get("document_id")
        if isinstance(doc_id, list):
            if cand_id in doc_id:
                filtered_combined.append(c)
            else:
                logger.warning(f"SECURITY ALERT: Cross-document contamination detected in merged chunks! Discarded chunk from {cand_id} because it is not in the allowed list {doc_id}.")
        else:
            if cand_id == doc_id:
                filtered_combined.append(c)
            else:
                logger.warning(f"SECURITY ALERT: Cross-document contamination detected in merged chunks! Discarded chunk from {cand_id} because it does not match active {doc_id}.")
    combined = filtered_combined

    if diagnostic_info is not None:
        diagnostic_info["expanded_section_chunks"] = len(expanded_section_chunks)
        diagnostic_info["expanded_neighbor_chunks"] = len(expanded_neighbor_chunks)
        diagnostic_info["total_retrieved"] = len(combined)

    return combined
