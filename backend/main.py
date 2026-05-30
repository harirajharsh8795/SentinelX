from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.routes import router
from api.auth import router as auth_router
from api.stream import router as stream_router
from utils.config import settings
from utils.logger import get_logger
from database.database import engine, SessionLocal
from database import models
from services.auth_service import get_password_hash

logger = get_logger(__name__)

# Create database tables + run lightweight migrations
models.Base.metadata.create_all(bind=engine)
from database.migrate import run_migrations
run_migrations()

from contextlib import asynccontextmanager
from database.database import get_db_context

def seed_users():
    with get_db_context() as db:
        default_users = [
            {"username": "admin", "role": "Admin", "password": "password123"},
            {"username": "auditor", "role": "Auditor", "password": "password123"},
            {"username": "officer", "role": "Officer", "password": "password123"},
        ]
        for u in default_users:
            user = db.query(models.User).filter(models.User.username == u["username"]).first()
            if not user:
                user = models.User(
                    username=u["username"],
                    role=u["role"],
                    hashed_password=get_password_hash(u["password"])
                )
                db.add(user)
            else:
                # Do NOT overwrite existing user passwords or roles on startup.
                pass
        db.commit()

seed_users()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.corpus_ingestion_service import seed_regulatory_sources, ingest_all_corpus
    seed_regulatory_sources()
    if settings.auto_seed_corpus:
        with get_db_context() as db:
            corpus_count = db.query(models.Document).filter(
                models.Document.ingestion_type == "corpus"
            ).count()
        if corpus_count == 0:
            import asyncio
            async def _bg_seed():
                result = await asyncio.to_thread(ingest_all_corpus, force=False)
                logger.info("Auto-seeded corpus: %s documents", result.get("total_ingested", 0))
            asyncio.create_task(_bg_seed())

    start_scheduler()
    logger.info("Application startup complete.")
    yield
    from services.scheduler_service import scheduler
    try:
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully.")
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {e}")

app = FastAPI(title="SentinelX", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5200", "http://127.0.0.1:5200", "http://localhost:5173", "http://localhost:5199"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Phase 12: Rate Limiting Middleware
from utils.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=150)

from utils.observability_middleware import ObservabilityMiddleware
app.add_middleware(ObservabilityMiddleware)

# Phase 11: APScheduler
from services.scheduler_service import start_scheduler

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(router, prefix="/api")
app.include_router(stream_router, prefix="/api")

@app.get("/")
def root():
    logger.info("Health check")
    return {"status": "ok", "service": "SentinelX"}
