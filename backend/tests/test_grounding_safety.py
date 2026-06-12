import pytest
from services.observability_service import estimate_grounding_quality

def test_grounding_clean_supported():
    sources = [
        {"snippet": "The Reserve Bank of India has updated the customer identification process.", "text": "The Reserve Bank of India has updated the customer identification process.", "score": 0.9}
    ]
    res = estimate_grounding_quality("The Reserve Bank of India has updated the customer identification process. (Source 1).", sources)
    # Grounding score should be high and reply intact
    assert res["grounding_score"] >= 0.85
    assert "customer identification process" in res["validated_reply"]
    assert "(Source 1)" in res["validated_reply"]

def test_grounding_citation_correction():
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.85},
        {"snippet": "Some unrelated info about audits.", "text": "Some unrelated info about audits.", "score": 0.5}
    ]
    # Wrong citation: cites (Source 2) but is in Source 1
    res = estimate_grounding_quality("Video KYC onboarding is now live. (Source 2).", sources)
    # The citation should be corrected to (Source 1)
    assert "(Source 1)" in res["validated_reply"]
    assert "(Source 2)" not in res["validated_reply"]

def test_grounding_unsupported_removal():
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.85}
    ]
    # One supported sentence, one unsupported sentence
    reply = "Video KYC onboarding is now live. (Source 1). The stock market index increased by ten percent."
    res = estimate_grounding_quality(reply, sources)
    # The unsupported sentence should be removed from validated reply
    assert "Video KYC onboarding" in res["validated_reply"]
    assert "stock market" not in res["validated_reply"]

def test_grounding_fake_clause_removal():
    sources = [
        {"snippet": "Under Section 11, banks must report incidents.", "text": "Under Section 11, banks must report incidents.", "score": 0.9}
    ]
    # Text matches Section 11 but LLM claims Section 99
    reply = "Under Section 99, banks must report incidents. (Source 1)."
    res = estimate_grounding_quality(reply, sources)
    # The fake clause sentence should be removed, resulting in no evidence fallback
    assert res["validated_reply"] == "Not explicitly stated in the document."

def test_grounding_no_evidence_fallback():
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.8}
    ]
    res = estimate_grounding_quality("Completely random ungrounded answer.", sources)
    assert res["validated_reply"] == "Not explicitly stated in the document."
