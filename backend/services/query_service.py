"""
Query service — executes validated SQL on the database and returns rows.
Includes automatic PostgreSQL → SQLite SQL rewriting when running on SQLite.
"""

from __future__ import annotations

import re
# pyrefly: ignore [missing-import]
from sqlalchemy import text

from config import settings
from database import engine
from utils.logger import get_logger

logger = get_logger(__name__)

# ── PostgreSQL → SQLite SQL rewrites ──────────────────────────────

_PG_TO_SQLITE_REWRITES: list[tuple[re.Pattern, str | callable]] = [
    # DATE_TRUNC('month', col) → strftime('%Y-%m', col)
    (re.compile(r"DATE_TRUNC\s*\(\s*'month'\s*,\s*(\w+(?:\.\w+)?)\s*\)", re.IGNORECASE),
     r"strftime('%Y-%m', \1)"),
    # DATE_TRUNC('year', col) → strftime('%Y', col)
    (re.compile(r"DATE_TRUNC\s*\(\s*'year'\s*,\s*(\w+(?:\.\w+)?)\s*\)", re.IGNORECASE),
     r"strftime('%Y', \1)"),
    # ROUND(expr::numeric, N) → ROUND(CAST(expr AS REAL), N)
    (re.compile(r"ROUND\((.+?)::numeric\s*,\s*(\d+)\)", re.IGNORECASE),
     r"ROUND(CAST(\1 AS REAL), \2)"),
    # expr::numeric → CAST(expr AS REAL)
    (re.compile(r"(\w+(?:\.\w+)?)::numeric", re.IGNORECASE),
     r"CAST(\1 AS REAL)"),
    # NOW() → datetime('now')
    (re.compile(r"\bNOW\(\)", re.IGNORECASE),
     "datetime('now')"),
    # INTERVAL 'N years'
    (re.compile(r">=\s*(?:NOW\(\)|datetime\('now'\)|CURRENT_DATE)\s*-\s*INTERVAL\s+'(\d+)\s*years'", re.IGNORECASE),
     r">= datetime('now', '-\1 years')"),
    (re.compile(r">=\s*(?:NOW\(\)|datetime\('now'\)|CURRENT_DATE)\s*-\s*INTERVAL\s+'(\d+)\s*months'", re.IGNORECASE),
     r">= datetime('now', '-\1 months')"),
    # DISTINCT ON (col) ... ORDER BY col, other DESC → GROUP BY subquery (best effort)
    (re.compile(r"DISTINCT\s+ON\s*\(\s*(\w+)\s*\)", re.IGNORECASE),
     r"DISTINCT"),
    # DATE 'YYYY-MM-DD' → 'YYYY-MM-DD'
    (re.compile(r"\bDATE\s+'(\d{4}-\d{2}-\d{2})'", re.IGNORECASE),
     r"'\1'"),
    # Boolean true → 1, false → 0
    (re.compile(r"\b=\s*true\b", re.IGNORECASE), "= 1"),
    (re.compile(r"\b=\s*false\b", re.IGNORECASE), "= 0"),
    (re.compile(r"\bIS\s+true\b", re.IGNORECASE), "= 1"),
    (re.compile(r"\bIS\s+false\b", re.IGNORECASE), "= 0"),
]


def _rewrite_for_sqlite(sql: str) -> str:
    """Apply PostgreSQL → SQLite SQL rewrites."""
    for pattern, replacement in _PG_TO_SQLITE_REWRITES:
        sql = pattern.sub(replacement, sql)
    return sql


def execute_query(sql: str) -> list[dict]:
    """
    Run a validated SELECT query and return results as a list of dicts.
    Automatically rewrites PostgreSQL-specific SQL for SQLite if needed.
    """
    # Rewrite SQL if we're on SQLite
    if "sqlite" in engine.dialect.name:
        sql = _rewrite_for_sqlite(sql)

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
        logger.error("Query execution failed: %s\nSQL: %s", exc, sql[:500])
        return []


def preview_rows(rows: list[dict], n: int = 5) -> str:
    """Return the first N rows as a readable string for LLM summarisation."""
    if not rows:
        return "No results returned."
    subset = rows[:n]
    lines = [str(r) for r in subset]
    trailer = f"\n… and {len(rows) - n} more rows." if len(rows) > n else ""
    return "\n".join(lines) + trailer
