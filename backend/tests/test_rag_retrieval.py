import pytest
from rag.hybrid_search import hybrid_search_and_rerank

def test_hybrid_retrieval_returns_valid_chunks():
    # Note: Requires ChromaDB to have test data initialized.
    # In a real CI pipeline, you would mock the Chroma client or use an in-memory test collection.
    
    # Passing dummy doc_id
    query = "cybersecurity penalty"
    results = hybrid_search_and_rerank(query, final_k=2, doc_id="dummy-test-id")
    
    # Even if empty, it shouldn't crash.
    assert isinstance(results, list)
    if len(results) > 0:
        assert "score" in results[0]
        assert "rerank_score" in results[0]
        assert "text" in results[0]
