import unicodedata
import pytest
from services.document_service import repair_hindi_text, normalize_text

def test_hindi_ocr_repair_rbi_variants():
    # List of corrupted variations of "भारतीय रिज़र्व बैंक" that commonly occur in OCR
    variants = [
        "भारतीय रज़वर् ब क",
        "भारतीय रज़र्व ब क",
        "भारतीय रज़र्व बैंक",
        "भारतीय रिज़र्व ब क",
        "भारतीय रज़वर् बैंक",
        "भारतीय रिज़वर् बैंक",
        "भारतीय रज़रर्व बैंक",
        "भारतीय रज़रव् बैंक",
        "भारतीय रज़र्व बैंक",
        "भारतीय रिज़र्व बैंक",
        "भारतीय रिज़र्व बँक",
        "भारतीय रिजर्व बैंक",
    ]
    
    expected = "भारतीय रिज़र्व बैंक"
    
    for variant in variants:
        repaired = repair_hindi_text(variant)
        assert repaired == expected, f"Failed to repair variant: {variant!r}. Got: {repaired!r}"

def test_hindi_ocr_repair_general():
    # Misplaced short 'i' matra (ि U+093F) handling
    corrupted_matra = "ववभाग"
    assert repair_hindi_text(corrupted_matra) == "विभाग"
    
    # Common double व U+0935 corruption to U+093F matra
    assert repair_hindi_text("वववेकाधीन") == "विवेकाधीन"
    
    # Normalization check
    text = "भारतीय रिज़र्व बैंक"
    normalized = normalize_text(text)
    assert normalized == expected_nfc(text)
    assert unicodedata.is_normalized('NFC', normalized)

def expected_nfc(text: str) -> str:
    return unicodedata.normalize('NFC', text)
