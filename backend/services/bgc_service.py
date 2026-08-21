"""
BGC service — USP 7.

Provides Bio-Geochemical Argo-specific query helpers:
  - Available BGC parameters for a float
  - BGC-specific chart type selection
  - Extend NL routing context for O2, Chl, pH, NO3 questions
"""

from __future__ import annotations

from services.query_service import execute_query
from utils.logger import get_logger

logger = get_logger(__name__)

BGC_PARAMS = {
    "dissolved_oxygen": {"unit": "µmol/kg", "label": "Dissolved Oxygen"},
    "chlorophyll": {"unit": "mg/m³", "label": "Chlorophyll-a"},
    "ph": {"unit": "pH (total scale)", "label": "pH"},
    "nitrate": {"unit": "µmol/kg", "label": "Nitrate"},
    "backscatter": {"unit": "m⁻¹", "label": "Backscatter (700nm)"},
}

BGC_CHART_MAP: dict[str, str] = {
    "dissolved_oxygen": "depth_profile",
    "chlorophyll":      "depth_profile",
    "ph":               "depth_profile",
    "nitrate":          "depth_profile",
}


def get_available_bgc_params(wmo_id: str) -> list[str]:
    """Return list of BGC parameters that have non-null data for a float."""
    sql = f"""
SELECT
    COUNT(dissolved_oxygen) AS cnt_o2,
    COUNT(chlorophyll)      AS cnt_chl,
    COUNT(ph)               AS cnt_ph,
    COUNT(nitrate)          AS cnt_no3,
    COUNT(backscatter)      AS cnt_bb
FROM bgc_profiles b
JOIN float_metadata fm ON b.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
LIMIT 1;
"""
    rows = execute_query(sql)
    if not rows:
        return []
    r = rows[0]
    return [
        p for p, key in [
            ("dissolved_oxygen", "cnt_o2"),
            ("chlorophyll", "cnt_chl"),
            ("ph", "cnt_ph"),
            ("nitrate", "cnt_no3"),
            ("backscatter", "cnt_bb"),
        ] if r.get(key, 0) > 0
    ]


def shape_bgc_profile(rows: list[dict], parameter: str) -> dict:
    """
    Shape BGC profile rows into a depth-profile chart payload
    specific to the requested parameter.
    """
    param_meta = BGC_PARAMS.get(parameter, {"unit": "", "label": parameter})
    sorted_rows = sorted(rows, key=lambda x: x.get("pressure", 0))

    return {
        "type": "depth_profile",
        "parameter": parameter,
        "label": param_meta["label"],
        "unit": param_meta["unit"],
        "traces": [{
            "name": param_meta["label"],
            "x": [r.get(parameter) for r in sorted_rows],
            "y": [r.get("pressure") for r in sorted_rows],
            "param": parameter,
        }],
    }


def bgc_summary_context(wmo_id: str) -> str:
    """Return a one-line context string for the LLM about available BGC params."""
    params = get_available_bgc_params(wmo_id)
    if not params:
        return f"Float {wmo_id} has no BGC data."
    labels = [BGC_PARAMS[p]["label"] for p in params if p in BGC_PARAMS]
    return f"Float {wmo_id} has BGC data for: {', '.join(labels)}."
