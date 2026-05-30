from __future__ import annotations

import re
import unicodedata
from typing import List, Dict, Any


def normalize_text(text: str) -> str:
    if not text:
        return ""
    # 1. NFC normalization
    text = unicodedata.normalize('NFC', text)
    # 2. Corrupted Unicode patterns remove (keep ASCII, Devanagari, and whitespace)
    text = re.sub(r'[^\x00-\x7F\u0900-\u097F\s]', ' ', text)
    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 3. Clean horizontal spaces while keeping block newlines intact
    lines = []
    for line in text.split("\n"):
        clean_line = re.sub(r'[ \t]+', ' ', line).strip()
        lines.append(clean_line)
    text = "\n".join(lines)
    # Collapse 3+ newlines to max 2
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
    text = normalize_text(text)
    blocks: List[Dict[str, str]] = []
    current: List[str] = []
    current_heading = "General"

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            if current:
                join_char = "\n" if any("|" in l for l in current) else " "
                blocks.append({"text": join_char.join(current).strip(), "heading": current_heading})
                current = []
            continue

        if _is_heading(line):
            if current:
                join_char = "\n" if any("|" in l for l in current) else " "
                blocks.append({"text": join_char.join(current).strip(), "heading": current_heading})
                current = []
            current_heading = line
            current.append(line)
            continue

        current.append(line)

    if current:
        join_char = "\n" if any("|" in l for l in current) else " "
        blocks.append({"text": join_char.join(current).strip(), "heading": current_heading})

    return [block for block in blocks if block["text"]]


def _chunk_table_block(block: Dict[str, str], chunk_size: int, overlap: int) -> List[Dict[str, str]]:
    lines = block["text"].split("\n")
    chunks = []
    current_lines = []
    current_len = 0
    heading = block["heading"]
    
    for line in lines:
        if current_len + len(line) + 1 > chunk_size and current_lines:
            chunks.append({"text": "\n".join(current_lines), "heading": heading})
            # Support overlap: keep last few lines if possible
            overlap_lines = []
            overlap_len = 0
            for ol in reversed(current_lines):
                if overlap_len + len(ol) + 1 < overlap:
                    overlap_lines.insert(0, ol)
                    overlap_len += len(ol) + 1
                else:
                    break
            current_lines = overlap_lines
            current_len = overlap_len
            
        current_lines.append(line)
        current_len += len(line) + 1
        
    if current_lines:
        chunks.append({"text": "\n".join(current_lines), "heading": heading})
    return chunks


def _chunk_large_block(block: Dict[str, str], chunk_size: int, overlap: int) -> List[Dict[str, str]]:
    text = block["text"].strip()
    heading = block["heading"]
    
    if "|" in text:
        return _chunk_table_block(block, chunk_size, overlap)
        
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
            else:
                space_boundary = text.rfind(" ", start, end)
                if space_boundary > start:
                    end = space_boundary + 1

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

    text = normalize_text(text)
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
        else:
            chunks.append({"text": current_text.strip(), "section_title": current_heading})
            current_text = block["text"]
            current_heading = block["heading"]

    if current_text.strip():
        chunks.append({"text": current_text.strip(), "section_title": current_heading})

    return [chunk for chunk in chunks if chunk["text"]]