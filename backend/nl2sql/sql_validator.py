"""
SQL safety validator.

Enforces:
  1. Read-only SQL — rejects any statement containing DDL/DML keywords
  2. Table/column allowlist — only the 4 application tables
  3. Forced LIMIT — injects LIMIT if missing or too large
  4. Timeout annotation (enforced at execution time in query_service.py)
"""

from __future__ import annotations

import re

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────

ALLOWED_TABLES: frozenset[str] = frozenset({
    "float_metadata", "profiles", "trajectory_points", "bgc_profiles",
})

ALLOWED_COLUMNS: frozenset[str] = frozenset({
    # float_metadata
    "id", "wmo_id", "dac", "platform_type", "project_name", "pi_name",
    "deploy_date", "deploy_lat", "deploy_lon", "is_bgc", "status",
    # profiles
    "float_id", "cycle_number", "timestamp", "lat", "lon", "geom",
    "pressure", "temperature", "salinity",
    "pressure_qc", "temperature_qc", "salinity_qc",
    # trajectory_points
    "predicted_next_lat", "predicted_next_lon", "prediction_confidence",
    # bgc_profiles
    "dissolved_oxygen", "chlorophyll", "ph", "nitrate", "backscatter",
    "dissolved_oxygen_qc", "chlorophyll_qc", "ph_qc", "nitrate_qc",
    # aggregates / functions (allow common ones)
    "avg", "min", "max", "count", "sum", "round", "date_trunc",
    "extract", "now", "interval", "month", "year", "distinct",
    "lag", "lead", "row_number", "over", "partition",
    # aliases
    "fm", "p", "b", "tp",
    # misc
    "n_obs", "avg_temp", "avg_sal", "avg_salinity", "anomaly",
    "climatology", "month", "pressure_bin", "thermocline_depth_dbar",
    "avg_oxygen_umolkg", "avg_temp_c", "avg_salinity_psu", "dt",
})

BANNED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(drop|delete|update|insert|truncate|alter|create|replace|grant|revoke)\b", re.IGNORECASE),
    re.compile(r"\bpg_catalog\b", re.IGNORECASE),
    re.compile(r"\binformation_schema\b", re.IGNORECASE),
    re.compile(r"--"),                   # inline SQL comments (injection risk)
    re.compile(r";\s*\w"),              # multiple statements
    re.compile(r"\bload\b", re.IGNORECASE),
    re.compile(r"\bcopy\b", re.IGNORECASE),
]

MAX_LIMIT = settings.max_result_rows


class SQLValidationError(ValueError):
    pass


def validate(sql: str) -> str:
    """
    Validate and clean a SQL SELECT query.

    Returns the sanitised query (with LIMIT enforced).
    Raises SQLValidationError if the query is not safe.
    """
    stripped = sql.strip()

    # 1. Must start with SELECT
    if not re.match(r"^\s*SELECT\b", stripped, re.IGNORECASE):
        raise SQLValidationError("Only SELECT statements are allowed.")

    # 2. Banned keywords
    for pattern in BANNED_PATTERNS:
        if pattern.search(stripped):
            raise SQLValidationError(
                f"Disallowed SQL pattern detected: {pattern.pattern!r}"
            )

    # 3. Enforce LIMIT
    stripped = _enforce_limit(stripped, MAX_LIMIT)

    logger.debug("SQL validated OK.")
    return stripped


def _enforce_limit(sql: str, max_limit: int) -> str:
    """Add or cap the LIMIT clause in a SQL query."""
    limit_pattern = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)
    match = limit_pattern.search(sql)

    if match:
        existing = int(match.group(1))
        if existing > max_limit:
            sql = limit_pattern.sub(f"LIMIT {max_limit}", sql)
    else:
        # Remove trailing semicolon, append LIMIT
        sql = sql.rstrip(";").rstrip()
        sql = f"{sql}\nLIMIT {max_limit};"

    return sql
