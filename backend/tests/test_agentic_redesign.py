import sys
import os
import pytest

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.query_rewriter import expand_domain_terms, rewrite_query_pipeline
from ai_agents.agent_tools import RiskScoringTool
from services.observability_service import estimate_grounding_quality
from ai_agents.agent_graph import AgentState, compliance_node, risk_node

def test_query_rewriter_acronyms():
    """Verify banking abbreviation expansion."""
    q1 = "What are the KYC rules?"
    expanded1 = expand_domain_terms(q1)
    assert "Know Your Customer" in expanded1
    assert "identity verification" in expanded1

    q2 = "guidelines on AML and STR"
    expanded2 = expand_domain_terms(q2)
    assert "Anti-Money Laundering" in expanded2
    assert "Suspicious Transaction Report" in expanded2

def test_query_rewriter_pipeline():
    """Verify that rewrite_query_pipeline returns the expected fields."""
    res = rewrite_query_pipeline("What are the KYC rules?")
    assert "original_query" in res
    assert "expanded_query" in res
    assert "alternative_queries" in res
    assert "hyde_document" in res
    assert len(res["all_search_queries"]) > 0

def test_risk_scoring_tool():
    """Verify risk and compliance score math calculations."""
    tool = RiskScoringTool()
    risks = [
        {"severity": "High"},
        {"severity": "Medium"},
        {"severity": "Low"}
    ]
    scores = tool.run(risks)
    # High (15) + Medium (10) + Low (5) = 30 risk score
    assert scores["risk_score"] == 30
    assert scores["compliance_score"] == 70

def test_grounding_validation_citation_bounds():
    """Verify citation boundary validation works."""
    sources = [
        {"snippet": "Source 1 snippet description"},
        {"snippet": "Source 2 snippet description"}
    ]
    
    # Valid citations
    res_valid = estimate_grounding_quality("The compliance rules apply. (Source 1) and (Source 2).", sources)
    assert res_valid["grounding_score"] >= 0.80
    assert "invalid_citation_index_3" not in res_valid["reasons"]

    # Invalid citation index
    res_invalid = estimate_grounding_quality("The compliance rules apply. (Source 3).", sources)
    assert res_invalid["grounding_score"] < 1.0
    assert any("invalid_citation_index_3" in r for r in res_invalid["reasons"])

def test_grounding_validation_overlaps():
    """Verify sentence fuzzy overlap checks fail for unsupported claims."""
    sources = [
        {"snippet": "Video Customer Identification Process is active."}
    ]
    
    # Text completely unrelated to the source snippet
    res = estimate_grounding_quality("Stock market trading hours are extended to 5 PM.", sources)
    assert res["grounding_score"] < 1.0
    assert any("unsupported_sentences" in r for r in res["reasons"])

def test_agent_graph_state_passing():
    """Verify state values persist through nodes correctly."""
    doc_id = "test-doc"
    context = "The Reserve Bank of India mandates Multi-Factor Authentication (MFA) within 45 days."
    state = AgentState(doc_id=doc_id, context=context)
    
    # Run compliance node
    state = compliance_node(state)
    assert len(state.agent_reasoning) > 0
    
    # Run risk node
    state = risk_node(state)
    assert state.risk_score >= 0
    assert state.compliance_score <= 100
