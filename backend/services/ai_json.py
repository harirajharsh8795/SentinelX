import json
from typing import Any, Dict, List, Optional


def _extract_json_block(text: str) -> Optional[str]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def parse_json(text: str) -> Dict[str, Any]:
    block = _extract_json_block(text) or "{}"
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        return {}


def parse_json_with_retry(
    prompt: str,
    schema_hint: str = "",
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Phase 4: Retry malformed JSON from LLM with a repair prompt.
    """
    from services.gemini_service import generate_text

    output = generate_text(prompt)
    data = parse_json(output)
    if data:
        return data

    repair_prompt = f"""The previous response was not valid JSON.
Return ONLY a valid JSON object. Required fields: {schema_hint or "as specified in original prompt"}.

Original request:
{prompt[:4000]}

Fix and return valid JSON only:"""

    for _ in range(max_retries):
        repaired = generate_text(repair_prompt)
        data = parse_json(repaired)
        if data:
            return data

    return {}


def to_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def get_str(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default
