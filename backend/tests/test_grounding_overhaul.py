import pytest
from services.observability_service import estimate_grounding_quality

def test_refusal_response_not_100_percent():
    # Requirements: Refusal responses must not display 100%. "Not explicitly stated" must never show 100% confidence.
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.95}
    ]
    
    # 1. Standard refusal phrasing
    res1 = estimate_grounding_quality("Not explicitly stated in the document.", sources)
    assert res1["grounding_state"] == "NOT_FOUND"
    assert res1["grounding_score"] == 0.0
    assert res1["confidence_score"] == 0.0
    
    # 2. Alternative refusal phrasing
    res2 = estimate_grounding_quality("The information is not found in the circular.", sources)
    assert res2["grounding_state"] == "NOT_FOUND"
    assert res2["grounding_score"] == 0.0
    assert res2["confidence_score"] == 0.0


def test_hallucination_near_0_percent():
    # Requirements: Hallucinations must display near 0% grounding and confidence.
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.85}
    ]
    
    # Completely unsupported answer (hallucination)
    res = estimate_grounding_quality("The RBI has banned all cryptocurrency trading in India.", sources)
    assert res["grounding_state"] == "UNSUPPORTED"
    assert res["grounding_score"] == 0.0
    assert res["confidence_score"] == 0.0


def test_grounding_and_confidence_independence():
    # Requirements: Grounding and confidence must be independent.
    # We assert that a response with low chunk similarity scores can be 100% grounded (SUPPORTED state),
    # while its confidence score remains low (matching the low chunk score), showing they are computed independently.
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.55}
    ]
    
    res = estimate_grounding_quality("Video KYC onboarding is now live. (Source 1).", sources)
    assert res["grounding_state"] == "SUPPORTED"
    assert res["grounding_score"] == 1.0          # 100% grounded
    assert res["confidence_score"] == 0.55        # But confidence is only 55% (independent of grounding score)


def test_partially_supported_state():
    # Requirements: Verify PARTIALLY_SUPPORTED state is assigned when some claims are supported and others are not.
    sources = [
        {"snippet": "Video KYC onboarding is now live.", "text": "Video KYC onboarding is now live.", "score": 0.90}
    ]
    
    # One supported sentence, one unsupported sentence
    reply = "Video KYC onboarding is now live. (Source 1). The stock market index increased."
    res = estimate_grounding_quality(reply, sources)
    assert res["grounding_state"] == "PARTIALLY_SUPPORTED"
    assert res["grounding_score"] == 0.50          # 1 out of 2 sentences supported
    assert res["confidence_score"] == 0.45         # Average of 0.90 and 0.0 is 0.45


def test_unknown_state_fallbacks():
    # Verify UNKNOWN state is assigned for empty or invalid parameter scenarios
    res_empty_reply = estimate_grounding_quality("", [{"snippet": "test", "score": 0.9}])
    assert res_empty_reply["grounding_state"] == "UNKNOWN"
    assert res_empty_reply["grounding_score"] == 0.0
    assert res_empty_reply["confidence_score"] == 0.0

    res_no_sources = estimate_grounding_quality("Some answer", [])
    assert res_no_sources["grounding_state"] == "UNKNOWN"
    assert res_no_sources["grounding_score"] == 0.0
    assert res_no_sources["confidence_score"] == 0.0
