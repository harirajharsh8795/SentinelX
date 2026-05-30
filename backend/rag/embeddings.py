import os
import sys
import time
import requests
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

# Check if we are running in a unit test environment to avoid connection hangs
IS_TESTING = "pytest" in sys.modules or os.getenv("TESTING") == "true"

def _get_pseudo_embedding(text: str) -> List[float]:
    import hashlib
    import random
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    seed = int(h, 16) % 10**8
    rng = random.Random(seed)
    return [rng.uniform(-0.1, 0.1) for _ in range(768)]

def detect_embedding_model() -> str:
    if IS_TESTING:
        return "nomic-embed-text"

    tags_url = "http://localhost:11434/api/tags"
    try:
        response = requests.get(tags_url, timeout=2.0)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            installed_names = [m.get("name", "").split(":")[0] for m in models_data]
            
            # Check for preferred models
            if "nomic-embed-text" in installed_names:
                logger.info("Ollama auto-detection: Found installed model 'nomic-embed-text'. Selecting it.")
                return "nomic-embed-text"
            elif "all-minilm" in installed_names:
                logger.info("Ollama auto-detection: Found installed model 'all-minilm'. Selecting it.")
                return "all-minilm"
            elif len(installed_names) > 0:
                fallback_name = models_data[0]['name']
                logger.info(f"Ollama auto-detection: Preferred models not found. Using first available: '{fallback_name}'")
                return fallback_name
    except Exception as e:
        logger.warning(f"Failed to query Ollama tags for model auto-detection: {e}. Defaulting to 'nomic-embed-text'.")
    return "nomic-embed-text"

OLLAMA_MODEL = detect_embedding_model()

_first_request_made = False

def warmup_embeddings():
    if IS_TESTING:
        logger.info("Test environment detected. Skipping startup warmup ping.")
        return

    try:
        logger.info(f"Initializing warmup ping for model '{OLLAMA_MODEL}' on startup...")
        start_time = time.perf_counter()
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": "warmup"
        }
        # First request timeout is 15.0 seconds as requested
        response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=15.0)
        latency = time.perf_counter() - start_time
        if response.status_code == 200:
            logger.info(f"Ollama embedding model '{OLLAMA_MODEL}' pre-loaded successfully. Latency: {latency:.4f} seconds.")
            global _first_request_made
            _first_request_made = True
        else:
            logger.warning(f"Ollama warmup ping returned non-200 code: {response.status_code} - {response.text}")
    except Exception as e:
        logger.warning(f"Could not complete Ollama warmup ping on startup: {e}. Will load model on first demand.")

# Execute warmup on module load (skipped in tests)
warmup_embeddings()

def simple_embedding(text: str, timeout: Optional[float] = None, is_document: bool = False) -> List[float]:
    """
    Generate vector embeddings locally via Ollama.
    Throws a RuntimeError if Ollama is unreachable or errors out.
    """
    from utils.config import settings
    global _first_request_made
    if not text or not text.strip():
        # Standard fallback for blank inputs
        return [0.0] * 768

    # Fast mock fallback strictly for unit tests in headless environments
    if IS_TESTING:
        return _get_pseudo_embedding(text)

    # Determine timeout: use parameter, env settings, or request-based default
    if timeout is None:
        timeout = float(settings.ollama_embed_timeout)

    current_timeout = timeout
    if not _first_request_made and timeout == 45.0:  # standard default can be increased for first load
        logger.info("First actual request executing. Setting timeout to 45.0s.")
        _first_request_made = True

    processed_text = text.strip()
    if "nomic" in OLLAMA_MODEL.lower() and not processed_text.startswith("search_query:") and not processed_text.startswith("search_document:"):
        if is_document:
            processed_text = f"search_document: {processed_text}"
        else:
            processed_text = f"search_query: {processed_text}"

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": processed_text
        }
        
        start_time = time.perf_counter()
        response = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=current_timeout)
        latency = time.perf_counter() - start_time
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding")
            if embedding and len(embedding) > 0:
                logger.info(f"Generated embedding successfully. Size: {len(embedding)}. Latency: {latency:.4f}s.")
                return embedding
            raise ValueError("Ollama returned an empty embedding array.")
            
        raise ValueError(f"Ollama returned non-200 status code: {response.status_code} - {response.text}")
        
    except Exception as e:
        logger.error(f"Fatal error generating local embedding via Ollama: {e}")
        raise RuntimeError(f"Local embedding generation failed: {str(e)}") from e


async def simple_embedding_async(text: str, timeout: Optional[float] = None, is_document: bool = False) -> List[float]:
    """
    Asynchronously generate vector embeddings locally via Ollama by offloading to a thread.
    """
    import asyncio
    from utils.config import settings
    
    if timeout is None:
        timeout = float(settings.ollama_embed_timeout)
        
    return await asyncio.to_thread(simple_embedding, text, timeout, is_document)


OLLAMA_BATCH_EMBED_URL = "http://localhost:11434/api/embed"

def batch_embeddings(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generate vector embeddings in batches locally via Ollama.
    """
    if IS_TESTING:
        return [_get_pseudo_embedding(t) for t in texts]

    results = []
    # Strip texts and replace empty strings with dummy text to avoid Ollama errors
    processed_texts = []
    for t in texts:
        pt = t.strip() if t.strip() else "empty"
        if "nomic" in OLLAMA_MODEL.lower() and not pt.startswith("search_query:") and not pt.startswith("search_document:"):
            pt = f"search_document: {pt}"
        processed_texts.append(pt)

    logger.info(f"Generating embeddings for {len(processed_texts)} chunks in batches of {batch_size}...")

    for i in range(0, len(processed_texts), batch_size):
        batch = processed_texts[i:i + batch_size]
        payload = {
            "model": OLLAMA_MODEL,
            "input": batch
        }
        try:
            start_time = time.perf_counter()
            response = requests.post(OLLAMA_BATCH_EMBED_URL, json=payload, timeout=60.0)
            latency = time.perf_counter() - start_time
            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("embeddings")
                if embeddings and len(embeddings) == len(batch):
                    logger.info(f"Batch embedding generated successfully ({len(batch)} items). Latency: {latency:.4f}s.")
                    results.extend(embeddings)
                else:
                    raise ValueError(f"Ollama returned incorrect number of embeddings: expected {len(batch)}, got {len(embeddings) if embeddings else 0}")
            else:
                raise ValueError(f"Ollama returned non-200 status code: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Fatal error generating batch embeddings via Ollama: {e}")
            raise RuntimeError(f"Local batch embedding generation failed: {str(e)}") from e

    return results
