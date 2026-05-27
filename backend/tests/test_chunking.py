import pytest
from rag.semantic_chunker import chunk_text

def test_chunking_with_headings():
    sample_text = """
SECTION 1: Introduction
This is the introduction segment. It should be bundled under the General heading or Section 1.

SECTION 2: Compliance Requirements
Banks must ensure that all systems are patched within 30 days. Logs must be retained for 90 days.
"""
    chunks = chunk_text(sample_text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 0
    # Check if section title was captured
    titles = [chunk["section_title"] for chunk in chunks]
    assert "SECTION 2: Compliance Requirements" in titles
