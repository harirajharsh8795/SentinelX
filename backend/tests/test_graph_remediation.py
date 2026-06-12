import pytest
from unittest.mock import MagicMock, patch
from models.schemas import GraphNode
from services.graph_service import _enrich_nodes_with_sources
from services.chat_service import chat_with_document

def test_graph_node_schema_additional_fields():
    # Verify that the schema is expanded with new fields and allows serialization of list/metadata attributes
    node = GraphNode(
        id="node_1",
        label="Test Node",
        type="Rule",
        chunk_ids=["doc-1"],
        neighbor_chunk_ids=["doc-0", "doc-2"],
        section_metadata=["Section 1"],
        document_id="doc_id_123",
        source_text="This is test text."
    )
    assert node.chunk_ids == ["doc-1"]
    assert node.neighbor_chunk_ids == ["doc-0", "doc-2"]
    assert node.section_metadata == ["Section 1"]
    assert node.document_id == "doc_id_123"
    assert node.source_text == "This is test text."

    # Verify defaults are assigned correctly
    node_default = GraphNode(id="node_2", label="Test Defaults", type="Risk")
    assert node_default.chunk_ids == []
    assert node_default.neighbor_chunk_ids == []
    assert node_default.section_metadata == []
    assert node_default.document_id is None
    assert node_default.source_text == ""


def test_enrich_nodes_with_sources_top_n_and_neighbors():
    # Set up some dummy chunks
    chunks = [
        {"id": "doc1-0", "text": "This is KYC baseline rules chunk", "section_title": "KYC Introduction", "chunk_index": 0},
        {"id": "doc1-1", "text": "This is KYC Video-based Customer Identification Process (V-CIP) onboarding rule details", "section_title": "V-CIP Guidelines", "chunk_index": 1},
        {"id": "doc1-2", "text": "This is KYC AML suspicious transaction check details", "section_title": "AML Section", "chunk_index": 2},
    ]

    nodes = [
        {"id": "node_vcip", "label": "V-CIP customer onboarding", "type": "Rule"}
    ]

    # Enrich nodes
    enriched = _enrich_nodes_with_sources(nodes, chunks, document_id="doc1")
    node = enriched[0]

    # Verify top matched chunk is chunk index 1 (due to V-CIP / onboarding words overlap)
    assert "doc1-1" in node["chunk_ids"]
    assert node["source_section"] == "V-CIP Guidelines"
    assert "V-CIP Guidelines" in node["section_metadata"]
    
    # Verify neighbor chunk IDs are computed correctly (0 and 2)
    assert "doc1-0" in node["neighbor_chunk_ids"]
    assert "doc1-2" in node["neighbor_chunk_ids"]
    assert node["document_id"] == "doc1"


@pytest.mark.asyncio
@patch("services.chat_service.SessionLocal")
@patch("services.chat_service.doc_has_aml_content")
@patch("services.chat_service.get_chat_history")
@patch("services.chat_service.rewrite_query")
@patch("services.chat_service.hybrid_search_and_rerank")
@patch("services.chat_service.generate_text_async")
@patch("services.observability_service.estimate_grounding_quality")
@patch("rag.retriever.get_collection")
async def test_chat_graph_mode_prefix_repair_and_neighbor_expansion(
    mock_get_coll, mock_quality, mock_generate, mock_hybrid, mock_rewrite, mock_history, mock_aml, mock_session
):
    # Mock database session and document
    mock_doc = MagicMock()
    mock_doc.regulator = "RBI"
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
    mock_session.return_value = mock_db
    
    mock_aml.return_value = False
    mock_history.return_value = "No previous conversation"
    mock_rewrite.return_value = "rewritten query"
    mock_generate.return_value = "According to Section 3.2, V-CIP must be performed (Source 1)."
    mock_hybrid.return_value = []
    
    mock_quality.return_value = {
        "risk": "low",
        "validated_reply": "According to Section 3.2, V-CIP must be performed (Source 1).",
        "grounding_score": 1.0
    }

    # Mock collection get:
    # First get fetches the target chunk (index 1)
    # Second get fetches the neighbors (index 0 and 2)
    mock_collection = MagicMock()
    
    def side_effect_get(ids=None, include=None):
        if not ids:
            return {"documents": [], "metadatas": [], "ids": []}
        
        # Check if the IDs list has the active-doc prefix (testing prefix repair)
        for val in ids:
            assert val.startswith("active-doc-")
            
        if "active-doc-1" in ids:
            return {
                "ids": ["active-doc-1"],
                "documents": ["V-CIP is done remotely via secure video connection."],
                "metadatas": [{"doc_id": "active-doc", "chunk_index": 1, "section_title": "Section 3.2"}]
            }
        elif "active-doc-0" in ids or "active-doc-2" in ids:
            return {
                "ids": ["active-doc-0", "active-doc-2"],
                "documents": ["Pre-requisites for customer onboarding.", "Post onboarding verification process."],
                "metadatas": [
                    {"doc_id": "active-doc", "chunk_index": 0, "section_title": "Section 3.1"},
                    {"doc_id": "active-doc", "chunk_index": 2, "section_title": "Section 3.3"}
                ]
            }
        return {"documents": [], "metadatas": [], "ids": []}

    mock_collection.get.side_effect = side_effect_get
    mock_get_coll.return_value = mock_collection

    # We send stale chunk IDs: 'stale-doc-1'
    result = await chat_with_document(
        doc_id="active-doc",
        message="how is V-CIP performed",
        chunk_ids=["stale-doc-1"],
        graph_context_mode=True
    )

    # 1. Verify prefix was auto-repaired to 'active-doc-1'
    # 2. Verify sources contain the repaired chunk AND neighbor chunks
    assert len(result["sources"]) > 0
    # There should be neighbor expansions fetched
    assert result["debug"]["diagnostics"]["expanded_neighbor_chunks"] > 0
    assert result["grounded"] is True


@pytest.mark.asyncio
@patch("services.chat_service.SessionLocal")
@patch("services.chat_service.doc_has_aml_content")
@patch("services.chat_service.get_chat_history")
@patch("services.chat_service.rewrite_query")
@patch("services.chat_service.hybrid_search_and_rerank")
@patch("services.chat_service.generate_text_async")
@patch("services.observability_service.estimate_grounding_quality")
@patch("rag.retriever.get_collection")
@patch("rag.retriever.search_similar")
async def test_chat_graph_mode_stale_detection_semantic_fallback(
    mock_search, mock_get_coll, mock_quality, mock_generate, mock_hybrid, mock_rewrite, mock_history, mock_aml, mock_session
):
    # Mock database session and document
    mock_doc = MagicMock()
    mock_doc.regulator = "RBI"
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
    mock_session.return_value = mock_db
    
    mock_aml.return_value = False
    mock_history.return_value = "No previous conversation"
    mock_rewrite.return_value = "rewritten query"
    mock_generate.return_value = "According to Section 3.2, V-CIP must be performed (Source 1)."
    mock_hybrid.return_value = []
    
    mock_quality.return_value = {
        "risk": "low",
        "validated_reply": "According to Section 3.2, V-CIP must be performed (Source 1).",
        "grounding_score": 1.0
    }

    # Mock collection get returning empty (triggering stale chunk fallback retrieval)
    mock_collection = MagicMock()
    mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
    mock_get_coll.return_value = mock_collection

    # Mock search_similar (semantic fallback)
    mock_search.return_value = [
        {
            "text": "Fallback retrieved chunk text",
            "metadata": {"doc_id": "active-doc", "chunk_index": 5, "section_title": "Section 4.1"},
            "score": 0.85
        }
    ]

    result = await chat_with_document(
        doc_id="active-doc",
        message="fallback testing message",
        chunk_ids=["stale-doc-99"],
        source_text="Legacy source text from stale node",
        graph_context_mode=True
    )

    # Verify semantic fallback was executed
    mock_search.assert_called_once()
    assert len(result["sources"]) > 0
    assert result["sources"][0]["section_title"] == "Section 4.1"
    assert result["grounded"] is True
