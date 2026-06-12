import pytest
from unittest.mock import MagicMock, patch
from rag.retriever import search_similar
from rag.hybrid_search import hybrid_search_and_rerank
from services.chat_service import chat_with_document

def test_search_similar_requires_doc_id():
    # If doc_id is missing, search_similar should return empty list to prevent leak
    results = search_similar(query="test", top_k=5, doc_id=None)
    assert results == []

@patch("rag.retriever.get_collection")
@patch("rag.retriever.simple_embedding")
def test_search_similar_contamination_prevention(mock_embed, mock_get_coll):
    mock_embed.return_value = [0.1] * 384
    
    # Mock ChromaDB query results with a contaminated chunk from a different doc_id
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Clean text", "Contaminated text"]],
        "metadatas": [[
            {"doc_id": "active-doc", "chunk_index": 0},
            {"doc_id": "other-doc", "chunk_index": 0}
        ]],
        "distances": [[0.1, 0.2]]
    }
    mock_get_coll.return_value = mock_collection
    
    # Query for "active-doc"
    results = search_similar(query="test", top_k=5, doc_id="active-doc")
    
    # Should only return the clean chunk and discard the contaminated chunk
    assert len(results) == 1
    assert results[0]["metadata"]["doc_id"] == "active-doc"
    assert results[0]["text"] == "Clean text"

@patch("rag.hybrid_search.get_collection")
@patch("rag.hybrid_search.search_similar")
@patch("rag.reranker.rerank_chunks")
def test_hybrid_search_rerank_contamination_prevention(mock_rerank, mock_search, mock_get_coll):
    # Mock search_similar returning a contaminated chunk (e.g. from neighbors expansion)
    mock_search.return_value = [
        {"text": "Clean", "metadata": {"doc_id": "active-doc", "chunk_index": 0}, "score": 0.1}
    ]
    mock_rerank.return_value = [
        {"text": "Clean", "metadata": {"doc_id": "active-doc", "chunk_index": 0}, "score": 0.1}
    ]
    
    # Mock neighbor fetch returning a contaminated chunk
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "documents": ["Foreign neighbor"],
        "metadatas": [{"doc_id": "other-doc", "chunk_index": 1}]
    }
    mock_get_coll.return_value = mock_collection
    
    results = hybrid_search_and_rerank(query="test", final_k=5, doc_id="active-doc")
    
    # Ensure foreign neighbor is discarded
    for r in results:
        assert r["metadata"]["doc_id"] == "active-doc"
        assert r["text"] != "Foreign neighbor"

@pytest.mark.asyncio
@patch("services.chat_service.SessionLocal")
@patch("services.chat_service.doc_has_aml_content")
@patch("services.chat_service.get_chat_history")
@patch("services.chat_service.rewrite_query")
@patch("services.chat_service.hybrid_search_and_rerank")
@patch("services.chat_service.generate_text_async")
@patch("rag.retriever.get_collection")
async def test_chat_graph_context_mode_isolation(
    mock_get_coll, mock_generate, mock_hybrid, mock_rewrite, mock_history, mock_aml, mock_session
):
    # Mock SessionLocal and document queries
    mock_doc = MagicMock()
    mock_doc.regulator = "RBI"
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
    mock_session.return_value = mock_db
    
    mock_aml.return_value = False
    mock_history.return_value = "No previous conversation"
    mock_rewrite.return_value = "rewritten query"
    mock_generate.return_value = "Mocked answer and reference (Source 1)."
    mock_hybrid.return_value = []
    
    # Mock ChromaDB node collection get returning a contaminated node chunk
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "documents": ["Contaminated node text"],
        "metadatas": [{"doc_id": "other-doc", "chunk_index": 99}]
    }
    mock_get_coll.return_value = mock_collection
    
    # Chat in graph mode
    result = await chat_with_document(
        doc_id="active-doc",
        message="what is penalty",
        chunk_ids=["other-doc-99"],
        graph_context_mode=True
    )
    
    # The contaminated chunk should have been discarded, resulting in empty sources or fallback
    assert len(result.get("sources", [])) == 0
