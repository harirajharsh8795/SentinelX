import pytest
from unittest.mock import MagicMock, patch
from rag.retriever import search_similar
from rag.hybrid_search import hybrid_search_and_rerank
from rag.reranker import cosine_similarity, chunk_similarity, rerank_chunks
from services.observability_service import estimate_grounding_quality

def test_cosine_similarity():
    # Identical vectors
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.01) == 1.0

    # Orthogonal vectors
    v3 = [1.0, 0.0]
    v4 = [0.0, 1.0]
    assert cosine_similarity(v3, v4) == 0.0

    # Opposite vectors
    v5 = [1.0, -1.0]
    v6 = [-1.0, 1.0]
    assert pytest.approx(cosine_similarity(v5, v6), 0.01) == -1.0

    # Empty inputs
    assert cosine_similarity([], v2) == 0.0

def test_chunk_similarity_fallback():
    # If embeddings are present, use cosine
    c1 = {"text": "A", "embedding": [1.0, 0.0]}
    c2 = {"text": "B", "embedding": [0.0, 1.0]}
    assert chunk_similarity(c1, c2) == 0.0

    # If embeddings are missing, fallback to Jaccard
    c3 = {"text": "apple banana"}
    c4 = {"text": "banana cherry"}
    assert chunk_similarity(c3, c4) == 1.0 / 3.0

@patch("rag.retriever.get_collection")
@patch("rag.retriever.simple_embedding")
def test_search_similar_stores_similarity_and_distance(mock_embed, mock_get_coll):
    mock_embed.return_value = [0.1] * 384
    
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Doc A", "Doc B"]],
        "metadatas": [[
            {"doc_id": "test-doc", "chunk_index": 0},
            {"doc_id": "test-doc", "chunk_index": 1}
        ]],
        "distances": [[0.1, 0.6]],
        "embeddings": [[[0.5]*384, [0.2]*384]]
    }
    mock_get_coll.return_value = mock_collection
    
    results = search_similar(query="test query", top_k=2, doc_id="test-doc")
    
    assert len(results) == 2
    # Verify score is true similarity (1.0 - dist)
    assert pytest.approx(results[0]["score"], 0.01) == 0.9
    assert pytest.approx(results[0]["distance"], 0.01) == 0.1
    assert results[0]["embedding"] == [0.5]*384

    assert pytest.approx(results[1]["score"], 0.01) == 0.4
    assert pytest.approx(results[1]["distance"], 0.01) == 0.6

@patch("rag.hybrid_search.get_collection")
@patch("rag.hybrid_search.search_similar")
@patch("services.query_rewriter.generate_hyde_doc")
@patch("services.query_rewriter.generate_multi_queries")
@patch("database.database.get_db_context")
def test_hybrid_search_query_decomposition_targets(
    mock_db, mock_multi, mock_hyde, mock_search, mock_get_coll
):
    mock_search.return_value = []
    mock_hyde.return_value = "HyDE hypothetical paragraph text"
    mock_multi.return_value = ["Query A", "Query B"]
    
    # Mock SQLite chat history fetch to return empty list
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.return_value.__enter__.return_value = mock_session

    diagnostic_info = {}
    
    # Use a long specific query without broad words to avoid broad query mode
    hybrid_search_and_rerank(
        query="What is the specific process for video based customer identification remote onboarding KYC?",
        final_k=5,
        doc_id="test-doc",
        diagnostic_info=diagnostic_info
    )
    
    # Assert query decomposition correctly populated diagnostic targets
    targets = diagnostic_info.get("query_targets", [])
    assert "HyDE hypothetical paragraph text" in targets
    assert "Query A" in targets
    assert "Query B" in targets
    assert len(targets) > 2

def test_observability_confidence_math_for_similarity():
    sources = [
        {"snippet": "Doc A", "text": "Doc A", "score": 0.85},
        {"snippet": "Doc B", "text": "Doc B", "score": 0.50}
    ]
    # Use direct text match 'Doc A' to satisfy fuzzy logic
    res = estimate_grounding_quality("Doc A. (Source 1).", sources)
    assert res["grounding_score"] >= 0.80
    assert res["risk"] == "low"
