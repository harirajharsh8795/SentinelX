from __future__ import annotations

import re
from typing import List, Dict, Any


def _normalize_text(text: str) -> str:
    # Basic normalization
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Clean PDF extraction noise / unreadable artifacts
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
    # eliminate multiple horizontal spaces without destroying logical block structure
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.replace(' .', '.').replace(' ,', ',')
    # Collapse 3+ newlines to max 2 to keep blocks readable
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.lower().startswith("section "):
        return True
    if stripped.endswith(":") and len(stripped) <= 120:
        return True
    if re.match(r"^(\d+(?:\.\d+)*)\s+[A-Z][A-Za-z0-9 ,:/&()\-]{2,}$", stripped):
        return True
    if len(stripped) <= 120 and stripped == stripped.upper() and any(ch.isalpha() for ch in stripped):
        return True
    return False


def _split_into_blocks(text: str) -> List[Dict[str, str]]:
    text = _normalize_text(text)
    blocks: List[Dict[str, str]] = []
    current: List[str] = []
    current_heading = "General"

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append({"text": " ".join(current).strip(), "heading": current_heading})
                current = []
            continue

        if _is_heading(line):
            if current:
                blocks.append({"text": " ".join(current).strip(), "heading": current_heading})
                current = []
            current_heading = line
            current.append(line)
            continue

        current.append(line)

    if current:
        blocks.append({"text": " ".join(current).strip(), "heading": current_heading})

    return [block for block in blocks if block["text"]]


def _chunk_large_block(block: Dict[str, str], chunk_size: int, overlap: int) -> List[Dict[str, str]]:
    text = block["text"].strip()
    heading = block["heading"]
    if len(text) <= chunk_size:
        return [{"text": text, "heading": heading}]

    chunks: List[Dict[str, str]] = []
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            boundary = max(
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("; ", start, end),
                text.rfind(": ", start, end),
            )
            if boundary > start + max(80, chunk_size // 2):
                end = boundary + 1

        piece = text[start:end].strip()
        if piece:
            chunks.append({"text": piece, "heading": heading})

        if end >= len(text):
            break

        start = max(0, end - overlap)
        if start >= end:
            start = end

    return chunks


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []

    blocks = _split_into_blocks(text)
    chunks: List[Dict[str, Any]] = []
    current_text = ""
    current_heading = "General"

    for block in blocks:
        if len(block["text"]) > chunk_size:
            if current_text:
                chunks.append({"text": current_text.strip(), "section_title": current_heading})
                current_text = ""
            
            large_chunks = _chunk_large_block(block, chunk_size, overlap)
            for lc in large_chunks:
                chunks.append({"text": lc["text"], "section_title": lc["heading"]})
            continue

        if not current_text:
            current_text = block["text"]
            current_heading = block["heading"]
            continue

        candidate = f"{current_text} {block['text']}".strip()
        if len(candidate) <= chunk_size:
            current_text = candidate
            # Keep the heading of the first block in this combined chunk
        else:
            chunks.append({"text": current_text.strip(), "section_title": current_heading})
            current_text = block["text"]
            current_heading = block["heading"]

    if current_text.strip():
        chunks.append({"text": current_text.strip(), "section_title": current_heading})

    return [chunk for chunk in chunks if chunk["text"]]