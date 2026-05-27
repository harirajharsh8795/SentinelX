"""
SentinelX Input Sanitizer — Prompt Injection Defense Layer

Yeh module PDF/document text ko sanitize karta hai BEFORE it enters any LLM prompt.
Common injection patterns ko strip karta hai, token overflow prevent karta hai,
aur suspicious content ko flag karta hai.

Security fixes:
1. Strips known prompt injection patterns (Ignore instructions, System:, [INST], etc.)
2. Limits chunk size to prevent context window overflow
3. Removes control characters and encoded payloads
4. Logs warnings when injection patterns are detected
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# INJECTION PATTERN REGISTRY
# Common LLM prompt injection strings that attackers embed in PDFs
# ==============================================================================
_INJECTION_PATTERNS = [
    # Direct instruction override attempts
    r"(?i)ignore\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions?|prompts?|rules?|context)",
    r"(?i)disregard\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions?|prompts?|rules?)",
    r"(?i)forget\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions?|prompts?|rules?)",
    r"(?i)override\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|rules?)",
    r"(?i)do\s+not\s+follow\s+(the\s+)?(previous|above|prior)\s+(instructions?|rules?)",

    # Role/system prompt hijacking
    r"(?i)^system\s*:",
    r"(?i)^assistant\s*:",
    r"(?i)^human\s*:",
    r"(?i)^user\s*:",
    r"(?i)\[INST\]",
    r"(?i)\[/INST\]",
    r"(?i)<<SYS>>",
    r"(?i)<</SYS>>",
    r"(?i)<\|system\|>",
    r"(?i)<\|user\|>",
    r"(?i)<\|assistant\|>",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",

    # Prompt leaking / exfiltration attempts
    r"(?i)repeat\s+(the\s+)?(system\s+)?prompt",
    r"(?i)show\s+(me\s+)?(the\s+)?(system\s+)?prompt",
    r"(?i)print\s+(the\s+)?(system\s+)?prompt",
    r"(?i)what\s+(is|are)\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?)",
    r"(?i)output\s+(the\s+)?(system\s+)?prompt",
    r"(?i)reveal\s+(your\s+)?(system\s+)?(prompt|instructions?)",

    # Jailbreak patterns
    r"(?i)you\s+are\s+now\s+(DAN|an?\s+unrestricted|a?\s+new|jailbroken)",
    r"(?i)act\s+as\s+if\s+you\s+have\s+no\s+(restrictions?|rules?|guidelines?)",
    r"(?i)pretend\s+(you\s+are|to\s+be)\s+(a\s+)?(different|new|unrestricted)",
    r"(?i)developer\s+mode\s+(enabled|activated|on)",

    # Code execution / data exfil
    r"(?i)execute\s+(the\s+following|this)\s+(code|command|script)",
    r"(?i)run\s+(the\s+following|this)\s+(code|command|script)",
    r"(?i)import\s+os\s*[;\n]",
    r"(?i)subprocess\.\s*(call|run|Popen)",
    r"(?i)eval\s*\(",
    r"(?i)exec\s*\(",
]

# Precompile for performance
_COMPILED_PATTERNS = [re.compile(p) for p in _INJECTION_PATTERNS]

# Maximum characters per sanitized chunk (prevents token overflow)
MAX_CHUNK_CHARS = 8000

# Maximum characters for full document context entering a prompt
MAX_CONTEXT_CHARS = 15000


def sanitize_document_text(
    text: str,
    max_chars: Optional[int] = None,
    source_label: str = "document"
) -> str:
    """
    Core sanitization function — PDF/document text ko clean karta hai
    before it enters any LLM prompt template.

    Kya karta hai:
    1. Null/empty check
    2. Control characters strip (tab/newline preserve, baaki hata do)
    3. Known injection patterns detect + strip with logging
    4. Encoded payload detection (base64, hex blocks)
    5. Token overflow prevention via character limit

    Args:
        text: Raw document text from PDF extraction
        max_chars: Maximum allowed characters (default: MAX_CONTEXT_CHARS)
        source_label: Label for logging (e.g., "pdf", "chunk", "context")

    Returns:
        Sanitized text safe for prompt injection
    """
    if not text:
        return ""

    if max_chars is None:
        max_chars = MAX_CONTEXT_CHARS

    original_length = len(text)
    injection_count = 0

    # Step 1: Strip NUL bytes and non-printable control characters
    # Tab (\t), newline (\n), carriage return (\r) ko preserve karo
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Step 2: Detect and neutralize injection patterns
    for pattern in _COMPILED_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            injection_count += len(matches)
            # Replace with safe marker instead of silently deleting
            text = pattern.sub('[BLOCKED_CONTENT]', text)

    if injection_count > 0:
        logger.warning(
            f"[SECURITY] Prompt injection patterns detected in {source_label}: "
            f"{injection_count} pattern(s) neutralized. Original length: {original_length} chars."
        )

    # Step 3: Detect suspicious encoded payloads
    # Base64 blocks longer than 200 chars (legitimate PDFs rarely have inline base64 text)
    base64_pattern = re.compile(r'[A-Za-z0-9+/]{200,}={0,2}')
    b64_matches = base64_pattern.findall(text)
    if b64_matches:
        logger.warning(
            f"[SECURITY] Suspicious base64 payload detected in {source_label}: "
            f"{len(b64_matches)} block(s) removed."
        )
        text = base64_pattern.sub('[ENCODED_CONTENT_REMOVED]', text)

    # Step 4: Remove suspiciously long hex strings (potential shellcode/data exfil)
    hex_pattern = re.compile(r'(?:0x)?[0-9a-fA-F]{64,}')
    hex_matches = hex_pattern.findall(text)
    if hex_matches:
        logger.warning(
            f"[SECURITY] Suspicious hex payload detected in {source_label}: "
            f"{len(hex_matches)} block(s) removed."
        )
        text = hex_pattern.sub('[HEX_CONTENT_REMOVED]', text)

    # Step 5: Token overflow prevention — hard truncate
    if len(text) > max_chars:
        logger.info(
            f"[SANITIZER] Truncating {source_label} from {len(text)} to {max_chars} chars "
            f"to prevent token overflow."
        )
        text = text[:max_chars] + "\n[...content truncated for safety]"

    # Step 6: Clean up any resulting double markers
    text = re.sub(r'(\[BLOCKED_CONTENT\]\s*){2,}', '[BLOCKED_CONTENT] ', text)

    return text.strip()


def sanitize_chunk(text: str, chunk_index: int = 0) -> str:
    """
    Individual chunk sanitization — retriever se aane wale har chunk ko sanitize karo.
    Smaller limit than full context.
    """
    return sanitize_document_text(
        text,
        max_chars=MAX_CHUNK_CHARS,
        source_label=f"chunk_{chunk_index}"
    )


def sanitize_user_query(query: str) -> str:
    """
    User chat query sanitization — chat input bhi check karo
    for injection attempts (less aggressive, short text).
    """
    if not query:
        return ""

    # Hard limit on query length
    if len(query) > 2000:
        logger.warning(f"[SECURITY] User query truncated from {len(query)} to 2000 chars.")
        query = query[:2000]

    # Check for injection patterns
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(query):
            logger.warning(
                f"[SECURITY] Prompt injection pattern detected in user query. Neutralizing."
            )
            query = pattern.sub('[BLOCKED]', query)

    return query.strip()


def is_content_suspicious(text: str) -> bool:
    """
    Quick boolean check — kya yeh text mein injection patterns hain?
    Use for pre-flight validation without modifying text.
    """
    if not text:
        return False
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False
