from typing import Optional

from utils.gemini import generate_text as gemini_generate_text


def generate_text(prompt: str, timeout: Optional[int] = None) -> str:
    t = timeout if timeout is not None else 60
    return gemini_generate_text(prompt, timeout=t)
