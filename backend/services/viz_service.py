"""
Viz service — shapes query result rows into frontend-ready data structures.

Outputs:
  - GeoJSON FeatureCollection (for MapView)
  - depth-profile series      (for DepthProfileChart)
  - time-series series        (for TimeSeriesChart)
  - generic table             (fallback / researcher mode)
"""

from __future__ import annotations

from utils.logger import get_logger

logger = get_logger(__name__)


# ── Type detection ────────────────────────────────────────────────

def detect_viz_type(rows: list[dict]) -> str:
    """
    Infer the best visualisation type from column names.

    Returns one of: "map", "depth_profile", "timeseries", "stat_card", "table"
    """
    if not rows:
        return "table"
    cols = set(rows[0].keys())

    if "lat" in cols and "lon" in cols and "cycle_number" in cols:
        return "map"
    if "pressure" in cols and ("temperature" in cols or "salinity" in cols
                               or "chlorophyll" in cols or "dissolved_oxygen" in cols):
        return "depth_profile"
    if "month" in cols or ("timestamp" in cols and len(rows) > 1):
        return "timeseries"

    # Single-value result → stat card (single row with at least one numeric column)
    if len(rows) == 1:
        numeric_cols = [
            c for c in cols
            if isinstance(rows[0].get(c), (int, float))
            and c not in ("n_obs", "cycle_number", "float_id", "id")
        ]
        if numeric_cols:
            return "stat_card"

    return "table"


# ── Formatters ────────────────────────────────────────────────────

def to_geojson(rows: list[dict]) -> dict:
    """Convert rows with lat/lon into a GeoJSON FeatureCollection."""
    features = []
    for r in rows:
        lat = r.get("lat")
        lon = r.get("lon")
        if lat is None or lon is None:
            continue
        props = {k: v for k, v in r.items() if k not in ("lat", "lon", "geom")}
        # Serialise datetime objects
        for k, v in props.items():
            if hasattr(v, "isoformat"):
                props[k] = v.isoformat()
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


def to_depth_profile(rows: list[dict]) -> dict:
    """
    Return Plotly-ready depth profile series.
    Multiple wmo_id values → multiple traces.
    """
    # Group by wmo_id if present, else single series
    groups: dict[str, list] = {}
    for r in rows:
        key = str(r.get("wmo_id", "float"))
        groups.setdefault(key, []).append(r)

    traces = []
    for label, group in groups.items():
        group_sorted = sorted(group, key=lambda x: x.get("pressure", 0))
        for param in ("temperature", "salinity", "dissolved_oxygen",
                      "chlorophyll", "ph", "nitrate"):
            values = [r.get(param) for r in group_sorted]
            if any(v is not None for v in values):
                traces.append({
                    "name": f"{label} – {param}",
                    "x": values,
                    "y": [r.get("pressure") for r in group_sorted],
                    "param": param,
                    "wmo_id": label,
                })
    return {"type": "depth_profile", "traces": traces}


def to_timeseries(rows: list[dict]) -> dict:
    """Return Plotly-ready time-series series."""
    time_col = next(
        (c for c in ("month", "timestamp") if c in (rows[0] if rows else {})), None
    )
    value_cols = [
        c for c in (rows[0].keys() if rows else [])
        if c not in (time_col, "n_obs") and isinstance(rows[0].get(c), (int, float, type(None)))
    ]
    series = []
    for col in value_cols:
        series.append({
            "name": col,
            "x": [str(r.get(time_col)) for r in rows],
            "y": [r.get(col) for r in rows],
        })
    return {"type": "timeseries", "series": series}


def to_stat_card(rows: list[dict]) -> dict:
    """Shape a single-row result into a stat card payload."""
    row = rows[0]
    # Pick the most relevant numeric column
    PARAM_PRIORITY = [
        "avg_temp_c", "avg_temp", "temperature",
        "avg_salinity_psu", "salinity",
        "avg_oxygen_umolkg", "dissolved_oxygen",
        "chlorophyll", "ph", "nitrate",
        "thermocline_depth_dbar", "pressure",
    ]
    param = None
    value = None
    for p in PARAM_PRIORITY:
        if p in row and isinstance(row[p], (int, float)):
            param = p
            value = row[p]
            break
    if param is None:
        # Fall back to first numeric column
        for k, v in row.items():
            if isinstance(v, (int, float)) and k not in ("n_obs", "cycle_number", "float_id", "id"):
                param = k
                value = v
                break

    # Build context label from remaining columns
    context_parts = []
    for k, v in row.items():
        if k != param and v is not None:
            if k == "wmo_id":
                context_parts.append(f"Float {v}")
            elif k == "month":
                context_parts.append(f"Month: {v}")
            elif k not in ("n_obs", "float_id", "id"):
                context_parts.append(f"{k}: {v}")
    context = " · ".join(context_parts[:3]) if context_parts else None

    return {
        "value": value,
        "param": param,
        "unit": None,   # frontend StatCard resolves units from param name
        "label": None,  # frontend StatCard resolves labels from param name
        "context": context,
    }


def shape_results(rows: list[dict]) -> dict:
    """
    Auto-detect viz type and return shaped data.

    Returns:
        {
          "viz_type": "map" | "depth_profile" | "timeseries" | "table",
          "data": <formatted payload>,
          "row_count": int,
        }
    """
    viz_type = detect_viz_type(rows)
    serialized_rows = _serialise(rows)
    if viz_type == "map":
        data = to_geojson(rows)
    elif viz_type == "depth_profile":
        data = to_depth_profile(rows)
    elif viz_type == "timeseries":
        data = to_timeseries(rows)
    elif viz_type == "stat_card":
        data = to_stat_card(rows)
    else:
        data = {"rows": serialized_rows}

    return {
        "viz_type": viz_type,
        "data": data,
        "raw_rows": serialized_rows,
        "row_count": len(rows),
    }


def _serialise(rows: list[dict]) -> list[dict]:
    """Convert datetime/other non-JSON-native values to strings."""
    out = []
    for r in rows:
        out.append({k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in r.items()})
    return out
