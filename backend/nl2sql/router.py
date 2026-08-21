"""
Query router — decides whether to use a pre-built SQL template or fall
back to LLM-based NL2SQL generation.

Routing logic
-------------
1. Tokenise the user question (lowercase, remove punctuation).
2. For each template, check if ALL words in any of its keyword sets appear
   in the question tokens.
3. If a template matches, attempt to fill its parameters.
4. If parameter extraction succeeds, return the filled SQL (fast path).
5. Otherwise fall back to query_generator.generate_sql (LLM path).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from nl2sql.template_queries import TEMPLATES
from nl2sql.sql_validator import validate, SQLValidationError
from utils.geo_utils import region_to_bbox, REGION_BOUNDS
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Default parameter values ──────────────────────────────────────

def _default_dates() -> tuple[str, str]:
    end = datetime.utcnow()
    start = end - timedelta(days=365 * 3)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _extract_wmo(text: str) -> str | None:
    """Extract a 7-digit WMO id from text."""
    match = re.search(r"\b(\d{7})\b", text)
    return match.group(1) if match else None


def _extract_cycle(text: str) -> int | None:
    """Extract a cycle number like 'cycle 45' or '#45'."""
    match = re.search(r"\bcycle\s*#?\s*(\d+)\b", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"#(\d+)\b", text)
    if match:
        return int(match.group(1))
    return None


def _detect_region(text: str) -> tuple[float, float, float, float] | None:
    """Return bounding box if a named region is mentioned."""
    text_lower = text.lower()
    for alias, key in {
        "arabian sea": "arabian_sea",
        "bay of bengal": "bay_of_bengal",
        "indian ocean": "indian_ocean",
        "arabian": "arabian_sea",
        "bengal": "bay_of_bengal",
        "lakshadweep": "lakshadweep",
        "andaman": "andaman_sea",
        "persian gulf": "persian_gulf",
    }.items():
        if alias in text_lower:
            return REGION_BOUNDS.get(key)
    return None


def _fill_params(template: dict, question: str) -> dict | None:
    """
    Attempt to fill template parameters from the question text.
    Returns a dict of params on success, None if required params are missing.
    """
    params = template["params"]
    filled: dict = {}

    date_start, date_end = _default_dates()
    bbox = _detect_region(question) or (-60.0, 30.0, 20.0, 120.0)  # default: Indian Ocean
    lat_min, lat_max, lon_min, lon_max = bbox

    for p in params:
        if p == "lat_min":   filled[p] = lat_min
        elif p == "lat_max": filled[p] = lat_max
        elif p == "lon_min": filled[p] = lon_min
        elif p == "lon_max": filled[p] = lon_max
        elif p == "date_start": filled[p] = date_start
        elif p == "date_end":   filled[p] = date_end
        elif p == "p_min":   filled[p] = 0
        elif p == "p_max":   filled[p] = 2000
        elif p == "wmo_id":
            wmo = _extract_wmo(question)
            if wmo is None:
                return None     # required but not found
            filled[p] = wmo
        elif p == "wmo_id_1":
            wmos = re.findall(r"\b(\d{7})\b", question)
            if len(wmos) < 2:
                return None
            filled["wmo_id_1"] = wmos[0]
            filled["wmo_id_2"] = wmos[1]
        elif p == "wmo_id_2":
            pass  # already filled above
        elif p == "cycle_number":
            cycle = _extract_cycle(question)
            if cycle is None:
                return None
            filled[p] = cycle

    return filled


def _tokenise(text: str) -> set[str]:
    return set(re.sub(r"[^\w\s]", " ", text.lower()).split())


def route(question: str) -> dict:
    """
    Route a question to either a template or LLM NL2SQL.

    Returns a dict:
        {
          "source":   "template" | "llm",
          "sql":      "<validated SQL>",
          "template": <template dict> | None,
          "params":   <filled params dict> | None,
        }
    """
    tokens = _tokenise(question)

    for tmpl in TEMPLATES:
        for keyword_set in tmpl["keywords"]:
            if keyword_set.issubset(tokens):
                params = _fill_params(tmpl, question)
                if params is not None:
                    try:
                        raw_sql = tmpl["sql"].format(**params)
                        validated_sql = validate(raw_sql)
                        logger.info("Template match: %s", tmpl["id"])
                        return {
                            "source": "template",
                            "sql": validated_sql,
                            "template": tmpl,
                            "params": params,
                        }
                    except (KeyError, SQLValidationError) as e:
                        logger.warning("Template '%s' fill failed: %s", tmpl["id"], e)

    # Fall through to LLM
    logger.info("No template matched — using LLM NL2SQL.")
    from vectorstore.chroma_client import get_chroma_client
    from nl2sql.query_generator import generate_sql

    schema_context = get_chroma_client().get_relevant_context(question)
    raw_sql = generate_sql(question, schema_context)
    validated_sql = validate(raw_sql)

    return {
        "source": "llm",
        "sql": validated_sql,
        "template": None,
        "params": None,
    }