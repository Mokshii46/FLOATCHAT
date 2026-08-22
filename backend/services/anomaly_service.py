"""
Anomaly service — USP 1.

Detects temperature/salinity/oxygen anomalies in a region using a rolling
z-score method and returns a human-readable narrative sentence.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from services.query_service import execute_query
from utils.geo_utils import REGION_BOUNDS
from utils.logger import get_logger

logger = get_logger(__name__)

Z_THRESHOLD = 2.0   # flag if |z| > 2.0


@dataclass
class AnomalyResult:
    region: str
    parameter: str
    latest_value: float
    climatology: float
    z_score: float
    severity: str           # "normal" | "warning" | "critical"
    narrative: str


def detect_anomaly(
    region: str = "bay_of_bengal",
    parameter: str = "temperature",
    pressure_max: float = 10.0,
    months_back: int = 36,
) -> AnomalyResult:
    """
    Compute z-score of the most recent monthly mean vs the climatology
    over the past `months_back` months for the given region and parameter.

    Uses SQLite-compatible SQL.
    """
    bbox = REGION_BOUNDS.get(region)
    if bbox is None:
        bbox = REGION_BOUNDS["indian_ocean"]
    lat_min, lat_max, lon_min, lon_max = bbox

    sql = f"""
SELECT strftime('%Y-%m', timestamp) AS month,
       AVG({parameter}) AS mean_val
FROM profiles
WHERE lat BETWEEN {lat_min} AND {lat_max}
  AND lon BETWEEN {lon_min} AND {lon_max}
  AND pressure BETWEEN 0 AND {pressure_max}
  AND {parameter} IS NOT NULL
  AND timestamp >= datetime('now', '-{months_back} months')
GROUP BY month
ORDER BY month DESC
LIMIT 60;
"""
    rows = execute_query(sql)

    if not rows or len(rows) < 2:
        return AnomalyResult(
            region=region, parameter=parameter,
            latest_value=0, climatology=0, z_score=0,
            severity="normal",
            narrative="Insufficient data to detect anomalies in this region."
        )

    values = [r["mean_val"] for r in rows if r["mean_val"] is not None]
    if len(values) < 2:
        return AnomalyResult(
            region=region, parameter=parameter,
            latest_value=0, climatology=0, z_score=0,
            severity="normal",
            narrative="Insufficient data to detect anomalies in this region."
        )

    latest_val = values[0]          # most recent month
    climatology = statistics.mean(values[1:])
    stdev = statistics.stdev(values[1:]) if len(values) > 2 else 1.0
    z = (latest_val - climatology) / stdev if stdev else 0.0

    severity = "normal"
    if abs(z) > Z_THRESHOLD * 1.5:
        severity = "critical"
    elif abs(z) > Z_THRESHOLD:
        severity = "warning"

    direction = "above" if z > 0 else "below"
    unit = "°C" if parameter == "temperature" else ("PSU" if parameter == "salinity" else "µmol/kg")
    change = abs(latest_val - climatology)

    narrative = (
        f"The {region.replace('_', ' ')} shows a recent {parameter} of "
        f"{latest_val:.2f}{unit}, which is {change:.2f}{unit} {direction} "
        f"the {months_back // 12}-year climatological mean ({climatology:.2f}{unit}). "
        f"Anomaly z-score: {z:.1f} ({'significant' if severity != 'normal' else 'within normal range'})."
    )

    return AnomalyResult(
        region=region, parameter=parameter,
        latest_value=latest_val, climatology=climatology,
        z_score=round(z, 2), severity=severity,
        narrative=narrative,
    )
