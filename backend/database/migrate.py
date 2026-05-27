"""Lightweight SQLite migrations for new enterprise columns."""
import logging
from sqlalchemy import inspect, text
from database.database import engine

logger = logging.getLogger(__name__)

ALL_MIGRATION_COLUMNS = {
    "documents": [
        ("regulator", "VARCHAR"),
        ("framework", "VARCHAR"),
        ("source_url", "VARCHAR"),
        ("ingestion_type", "VARCHAR DEFAULT 'upload'"),
        ("external_id", "VARCHAR"),
        ("analysis_result", "TEXT"),
        ("knowledge_graph", "TEXT"),
    ],
    "agent_logs": [
        ("document_id", "VARCHAR"),
    ],
    "audit_logs": [
        ("document_id", "VARCHAR"),
    ],
    "alerts": [
        ("document_id", "VARCHAR"),
    ],
}


def _column_exists(table: str, column: str) -> bool:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def run_migrations() -> None:
    with engine.begin() as conn:
        for table, columns in ALL_MIGRATION_COLUMNS.items():
            for col, col_type in columns:
                if not _column_exists(table, col):
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    logger.info(f"Added column {col} ({col_type}) to table {table}")

