import os
import time
import sqlite3
import asyncio
import logging
from contextlib import contextmanager
from typing import Callable, Any
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Database URL from environment via settings (no hardcoded paths)
from utils.config import settings
SQLALCHEMY_DATABASE_URL = settings.database_url

# Subclass Session to automatically retry database write/read queries on SQLite locked/timeout errors.
class RetryingSession(Session):
    def commit(self):
        max_attempts = 3
        delay = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                super().commit()
                return
            except (OperationalError, sqlite3.OperationalError) as e:
                if "locked" in str(e).lower() or "timeout" in str(e).lower():
                    if attempt < max_attempts:
                        logger.warning(f"Database locked on commit. Retrying {attempt}/{max_attempts} after {delay}s...")
                        time.sleep(delay)
                        continue
                raise e

    def execute(self, statement, params=None, *args, **kwargs):
        max_attempts = 3
        delay = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                return super().execute(statement, params, *args, **kwargs)
            except (OperationalError, sqlite3.OperationalError) as e:
                if "locked" in str(e).lower() or "timeout" in str(e).lower():
                    if attempt < max_attempts:
                        logger.warning(f"Database locked on execute. Retrying {attempt}/{max_attempts} after {delay}s...")
                        time.sleep(delay)
                        continue
                raise e

    def flush(self, objects=None):
        max_attempts = 3
        delay = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                super().flush(objects)
                return
            except (OperationalError, sqlite3.OperationalError) as e:
                if "locked" in str(e).lower() or "timeout" in str(e).lower():
                    if attempt < max_attempts:
                        logger.warning(f"Database locked on flush. Retrying {attempt}/{max_attempts} after {delay}s...")
                        time.sleep(delay)
                        continue
                raise e

from sqlalchemy.pool import StaticPool

# Create Engine with timeout argument passed to sqlite3.connect()
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    poolclass=StaticPool
)

# Listen for SQLite connections and enforce WAL mode
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

# Enforce our custom RetryingSession class
SessionLocal = sessionmaker(
    class_=RetryingSession,
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Global asyncio.Lock for all write operations
db_write_lock = asyncio.Lock()
_main_loop = None

def get_main_loop():
    global _main_loop
    if _main_loop is None:
        try:
            _main_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
    return _main_loop

def execute_write_serialized(func: Callable, *args, **kwargs) -> Any:
    """
    Executes a database write function under the asyncio.Lock().
    If called from a worker thread (e.g. inside asyncio.to_thread), it routes the execution
    to the main thread's event loop via run_coroutine_threadsafe to preserve asyncio.Lock's
    safety.
    Includes automatic retry logic on SQLite lock/operational errors.
    """
    max_attempts = 3
    delay = 1.0

    def _run_with_retry():
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except (OperationalError, sqlite3.OperationalError, Exception) as e:
                err_str = str(e).lower()
                if "locked" in err_str or "timeout" in err_str or "busy" in err_str:
                    if attempt < max_attempts:
                        logger.warning(f"Database locked/busy in execute_write_serialized. Retrying {attempt}/{max_attempts} after {delay}s...")
                        time.sleep(delay)
                        continue
                raise e

    loop = get_main_loop()
    if loop and loop.is_running():
        async def _locked_write():
            async with db_write_lock:
                return await asyncio.to_thread(_run_with_retry)
        
        future = asyncio.run_coroutine_threadsafe(_locked_write(), loop)
        return future.result()
    else:
        # Fallback if no event loop is running (e.g. CLI seeding or startup scripts)
        return _run_with_retry()

