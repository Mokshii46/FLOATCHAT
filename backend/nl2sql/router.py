"""
Decides how to turn a natural-language question into SQL:

  1. Try to match it against a hardcoded template (template_queries.py) and
     extract the params that template needs straight from the text (WMO
     ids, named regions, dates, depth). Fast, deterministic, demo-safe.
  2. If no template scores well enough OR a matched template is missing a
     required param, fall back to freeform NL2SQL (query_generator.py).

This is intentionally simple regex/keyword matching rather than another
LLM call — the whole point of templates is to be a fast, cheap, reliable
path that doesn't depend on the LLM being available.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from config import settings
from nl2sql.template_queries import TEMPLATES, Template
from nl2sql import query_generator

logger = logging.getLogger(__name__)

# Rough bounding boxes [lon_min, lon_max, lat_min, lat_max] for regions users
# are likely to name when talking about Indian Ocean ARGO data. Extend as needed.
REGION_BBOXES: dict[str, list[float]] = {
    "indian ocean": [20, 120, -40, 30],
    "arabian sea": [50, 78, 5, 25],
    "bay of bengal": [78, 100, 5, 22],
    "andaman sea": [92, 100, 5, 15],
    "equator": [40, 100, -5, 5],
    "equatorial indian ocean": [40, 100, -5, 5],
    "southern ocean": [20, 120, -60, -40],
    "red sea": [32, 44, 12, 30],
    "persian gulf": [48, 57, 24, 30],
    "off mumbai": [70, 74, 15, 20],
    "off chennai": [78, 84, 10, 16],
}

WMO_ID_RE = re.compile(r"\b\d{6,9}\b")
DEPTH_M_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m\b|meters|metres|dbar)", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
MONTH_NAMES = {
    m.lower(): i
    for i, m in enumerate(
        ["", "January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"]
    ) if m
}


@dataclass
class RouteResult:
    mode: str            # "template" | "freeform"
    sql: str
    params: dict = field(default_factory=dict)
    template_key: str | None = None
    explanation: str = ""


def _find_region_bbox(question: str) -> list[float] | None:
    q = question.lower()
    # longest name first so "bay of bengal" wins over a generic substring
    for name in sorted(REGION_BBOXES, key=len, reverse=True):
        if name in q:
            return REGION_BBOXES[name]
    return None


def _find_date_range(question: str) -> tuple[datetime, datetime] | None:
    q = question.lower()
    year_match = YEAR_RE.search(q)
    year = int(year_match.group()) if year_match else datetime.utcnow().year

    for name, num in MONTH_NAMES.items():
        if name in q:
            start = datetime(year, num, 1)
            end = datetime(year + 1, 1, 1) if num == 12 else datetime(year, num + 1, 1)
            return start, end

    if "last year" in q:
        end = datetime.utcnow()
        return end - timedelta(days=365), end
    if "last month" in q:
        end = datetime.utcnow()
        return end - timedelta(days=30), end
    if year_match:
        return datetime(year, 1, 1), datetime(year + 1, 1, 1)

    return None


def _find_depth_range(question: str) -> tuple[float, float] | None:
    q = question.lower()
    if "surface" in q:
        return 0, 20
    if "shallow" in q:
        return 0, 200
    if "deep" in q or "deepest" in q:
        return 1000, 6000
    m = DEPTH_M_RE.search(q)
    if m:
        depth = float(m.group(1))
        return max(depth - 50, 0), depth + 50
    return None


def _find_wmo_ids(question: str) -> list[str]:
    return WMO_ID_RE.findall(question)


def _score_template(t: Template, question: str) -> int:
    q = question.lower()
    return sum(1 for kw in t.keywords if kw in q)


def _try_extract_params(t: Template, question: str) -> dict | None:
    params: dict = {"row_limit": settings.max_result_rows}
    wmo_ids = _find_wmo_ids(question)
    bbox = _find_region_bbox(question)
    date_range = _find_date_range(question)
    depth_range = _find_depth_range(question)

    for p in t.required_params:
        if p == "wmo_id" and wmo_ids:
            params["wmo_id"] = wmo_ids[0]
        elif p == "wmo_id_a" and len(wmo_ids) >= 1:
            params["wmo_id_a"] = wmo_ids[0]
        elif p == "wmo_id_b" and len(wmo_ids) >= 2:
            params["wmo_id_b"] = wmo_ids[1]
        elif p in ("lon_min", "lon_max", "lat_min", "lat_max") and bbox:
            params["lon_min"], params["lon_max"], params["lat_min"], params["lat_max"] = bbox
        elif p in ("start_date", "end_date") and date_range:
            params["start_date"], params["end_date"] = date_range
        elif p in ("pressure_min", "pressure_max") and depth_range:
            params["pressure_min"], params["pressure_max"] = depth_range
        elif p == "pressure_max" and depth_range:
            params["pressure_max"] = depth_range[1]
        else:
            return None  # required param not found in the question — bail on this template

    return params


def route(question: str) -> RouteResult:
    candidates = sorted(TEMPLATES.values(), key=lambda t: _score_template(t, question), reverse=True)

    for t in candidates:
        if _score_template(t, question) == 0:
            break  # no more plausible matches, everything below also scores 0
        params = _try_extract_params(t, question)
        if params is not None:
            logger.info("Matched template '%s' for question: %r", t.key, question)
            return RouteResult(
                mode="template",
                sql=t.sql,
                params=params,
                template_key=t.key,
                explanation=f"Matched template '{t.key}': {t.description}",
            )

    logger.info("No template matched, falling back to freeform NL2SQL for: %r", question)
    sql, explanation = query_generator.generate_sql(question)
    return RouteResult(mode="freeform", sql=sql, params={}, explanation=explanation)