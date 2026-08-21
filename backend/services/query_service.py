"""
Query service — executes validated SQL on the database and returns rows.
"""

from __future__ import annotations

from sqlalchemy import text

from config import settings
from database import engine
from utils.logger import get_logger

logger = get_logger(__name__)


def execute_query(sql: str) -> list[dict]:
    """
    Run a validated SELECT query and return results as a list of dicts.
    """
    logger.debug("Executing SQL:\n%s", sql)
    try:
        with engine.connect() as conn:
            if "postgresql" in engine.dialect.name:
                try:
                    conn.execute(text(f"SET statement_timeout = '{settings.query_timeout_seconds * 1000}';"))
                except Exception:
                    pass
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

        logger.info("Query returned %d rows.", len(rows))
        return rows
    except Exception as exc:
        logger.error("Query execution failed: %s", exc)
        return []


def preview_rows(rows: list[dict], n: int = 5) -> str:
    """Return the first N rows as a readable string for LLM summarisation."""
    if not rows:
        return "No results returned."
    subset = rows[:n]
    lines = [str(r) for r in subset]
    trailer = f"\n… and {len(rows) - n} more rows." if len(rows) > n else ""
    return "\n".join(lines) + trailer
