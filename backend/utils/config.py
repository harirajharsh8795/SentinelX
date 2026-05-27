"""
SentinelX Configuration — Environment-Driven with Startup Validation

Sabhi secrets .env file se load hote hain. Koi bhi hardcoded value nahi.
Agar required env vars missing hain toh startup pe FAIL with clear error.
"""
import os
import sys
import secrets
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file (override=True ensures .env values take priority)
load_dotenv(override=True)


def _require_env(key: str, description: str) -> str:
    """
    Required environment variable fetch karo.
    Agar missing hai toh clear error message ke saath crash karo — 
    silently defaulting to insecure values is NOT acceptable.
    """
    value = os.getenv(key)
    if not value or value.strip() == "":
        print(
            f"\n{'='*60}\n"
            f"  ❌ FATAL: Required environment variable missing!\n"
            f"  Variable: {key}\n"
            f"  Purpose:  {description}\n\n"
            f"  Fix: Add {key}=<value> to your backend/.env file\n"
            f"  Template: See .env.example for reference\n"
            f"{'='*60}\n",
            file=sys.stderr
        )
        raise SystemExit(f"Missing required env var: {key}")
    return value.strip()


def _get_env(key: str, default: str) -> str:
    """Optional environment variable with safe default."""
    return os.getenv(key, default).strip()


class Settings:
    def __init__(self) -> None:
        # ======================================================================
        # REQUIRED SECRETS — App will REFUSE to start without these
        # ======================================================================
        self.secret_key = _require_env(
            "SECRET_KEY",
            "JWT signing key for authentication tokens"
        )

        # Validate SECRET_KEY strength
        if len(self.secret_key) < 16:
            logger.warning(
                "[SECURITY] SECRET_KEY is too short (< 16 chars). "
                "Generate a strong key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        # Gemini API key (required for cloud mode, optional for offline/Jetson mode)
        self.gemini_api_key = _get_env("GEMINI_API_KEY", "")
        if not self.gemini_api_key:
            logger.info(
                "[CONFIG] GEMINI_API_KEY not set — running in offline/local Ollama mode."
            )

        # ======================================================================
        # DATABASE — From .env, no hardcoded paths
        # ======================================================================
        self.database_url = _get_env("DATABASE_URL", "sqlite:///./sentinel_v2.db")

        # ======================================================================
        # OLLAMA (Local SLM) — For air-gapped Jetson deployment
        # ======================================================================
        self.ollama_url = _get_env("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = _get_env("OLLAMA_MODEL", "qwen2.5:1.5b")

        # ======================================================================
        # STORAGE PATHS — All configurable via .env
        # ======================================================================
        self.chroma_persist_dir = _get_env("CHROMA_PERSIST_DIR", "./vector_store")
        self.upload_dir = _get_env("UPLOAD_DIR", "./uploads")
        self.corpus_dir = _get_env("CORPUS_DIR", "./data/corpus")

        # ======================================================================
        # APPLICATION SETTINGS
        # ======================================================================
        self.scrape_enabled = _get_env("SCRAPING_ENABLED", "true").lower() in ("1", "true", "yes")
        self.scrape_interval_hours = int(_get_env("SCRAPE_INTERVAL_HOURS", "12"))
        self.auto_seed_corpus = _get_env("AUTO_SEED_CORPUS", "true").lower() in ("1", "true", "yes")

        # JWT Configuration
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(_get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

        # CORS Origins
        origins = _get_env(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5200,http://127.0.0.1:5173,http://localhost:5199,http://127.0.0.1:5199,http://localhost:4173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://127.0.0.1:5176"
        )
        self.allowed_origins = [o.strip() for o in origins.split(",") if o.strip()]

        # Log successful config load
        logger.info("[CONFIG] SentinelX configuration loaded successfully from .env")
        logger.info(f"[CONFIG] Database: {self.database_url}")
        logger.info(f"[CONFIG] Ollama: {self.ollama_url} (model: {self.ollama_model})")
        logger.info(f"[CONFIG] CORS origins: {len(self.allowed_origins)} allowed")


settings = Settings()
