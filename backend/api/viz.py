"""
GET /viz/map        — GeoJSON of all active float last positions
GET /viz/profile    — depth profile for a float + cycle
GET /viz/timeseries — monthly mean T/S for a region

All SQL is SQLite-compatible.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Any

from services.query_service import execute_query
from services.viz_service import to_geojson, to_depth_profile, to_timeseries

router = APIRouter()


@router.get("/map")
def viz_map(
    lat_min: float = Query(-90.0),
    lat_max: float = Query(90.0),
    lon_min: float = Query(-180.0),
    lon_max: float = Query(180.0),
) -> dict[str, Any]:
    sql = f"""
SELECT fm.wmo_id, fm.platform_type, fm.is_bgc, fm.dac,
       tp.lat, tp.lon, tp.cycle_number, tp.timestamp,
       tp.predicted_next_lat, tp.predicted_next_lon
FROM trajectory_points tp
JOIN float_metadata fm ON tp.float_id = fm.id
JOIN (
    SELECT float_id, MAX(cycle_number) AS max_cycle
    FROM trajectory_points
    GROUP BY float_id
) latest ON tp.float_id = latest.float_id AND tp.cycle_number = latest.max_cycle
WHERE tp.lat BETWEEN {lat_min} AND {lat_max}
  AND tp.lon BETWEEN {lon_min} AND {lon_max}
LIMIT 5000;
"""
    rows = execute_query(sql)
    return to_geojson(rows)


@router.get("/profile")
def viz_profile(
    wmo_id: str = Query(...),
    cycle_number: int = Query(...),
) -> dict[str, Any]:
    sql = f"""
SELECT p.pressure, p.temperature, p.salinity,
       p.temperature_qc, p.salinity_qc,
       fm.wmo_id
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND p.cycle_number = {cycle_number}
ORDER BY p.pressure
LIMIT 5000;
"""
    rows = execute_query(sql)
    return to_depth_profile(rows)


@router.get("/timeseries")
def viz_timeseries(
    lat_min: float = Query(5.0),
    lat_max: float = Query(25.0),
    lon_min: float = Query(55.0),
    lon_max: float = Query(77.0),
    parameter: str = Query("temperature"),
    months: int = Query(36, le=120),
) -> dict[str, Any]:
    col = parameter if parameter in ("temperature", "salinity") else "temperature"
    sql = f"""
SELECT strftime('%Y-%m', timestamp) AS month,
       ROUND(AVG({col}), 3) AS avg_val,
       COUNT(*) AS n_obs
FROM profiles
WHERE lat BETWEEN {lat_min} AND {lat_max}
  AND lon BETWEEN {lon_min} AND {lon_max}
  AND timestamp >= datetime('now', '-{months} months')
  AND {col} IS NOT NULL
GROUP BY month
ORDER BY month
LIMIT 200;
"""
    rows = execute_query(sql)
    return to_timeseries(rows)
