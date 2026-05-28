from typing import Optional

from utils.gemini import generate_text as gemini_generate_text
from utils.gemini import generate_text_async as gemini_generate_text_async


def generate_text(prompt: str, timeout: Optional[int] = None) -> str:
    t = timeout if timeout is not None else 20
    return gemini_generate_text(prompt, timeout=t)


async def generate_text_async(prompt: str, timeout: Optional[int] = None) -> str:
    t = timeout if timeout is not None else 45
    return await gemini_generate_text_async(prompt, timeout=t)

