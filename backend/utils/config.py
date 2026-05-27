import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./vector_store")
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        self.corpus_dir = os.getenv("CORPUS_DIR", "./data/corpus")
        self.scrape_enabled = os.getenv("SCRAPING_ENABLED", "true").lower() in ("1", "true", "yes")
        self.scrape_interval_hours = int(os.getenv("SCRAPE_INTERVAL_HOURS", "12"))
        self.auto_seed_corpus = os.getenv("AUTO_SEED_CORPUS", "true").lower() in ("1", "true", "yes")
        self.secret_key = os.getenv("SECRET_KEY", "supersecure-canara-sentinel-key-2026")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
        origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5200,http://127.0.0.1:5173,http://localhost:5199,http://127.0.0.1:5199,http://localhost:4173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://127.0.0.1:5176"
        )
        self.allowed_origins = [o.strip() for o in origins.split(",") if o.strip()]

settings = Settings()
