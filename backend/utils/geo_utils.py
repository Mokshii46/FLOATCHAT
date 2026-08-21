"""
Geographic utility helpers.

Converts human-readable region names to lat/lon bounding boxes and
provides common spatial helper functions used across NL2SQL templates
and the viz service.
"""

from typing import Optional

# Named ocean/sea regions → (lat_min, lat_max, lon_min, lon_max)
REGION_BOUNDS: dict[str, tuple[float, float, float, float]] = {
    "indian_ocean":       (-60.0,  30.0,  20.0, 120.0),
    "bay_of_bengal":      (  5.0,  22.0,  80.0,  98.0),
    "arabian_sea":        (  5.0,  25.0,  55.0,  77.0),
    "north_indian_ocean": (  0.0,  30.0,  45.0, 100.0),
    "south_indian_ocean": (-60.0,   0.0,  20.0, 120.0),
    "lakshadweep":        (  8.0,  14.0,  71.0,  75.0),
    "andaman_sea":        (  7.0,  15.0,  92.0,  99.0),
    "persian_gulf":       ( 23.0,  30.0,  48.0,  57.0),
}

# Alias normalisation
ALIASES: dict[str, str] = {
    "indian ocean":       "indian_ocean",
    "bay of bengal":      "bay_of_bengal",
    "arabian sea":        "arabian_sea",
    "north indian":       "north_indian_ocean",
    "south indian":       "south_indian_ocean",
    "andaman":            "andaman_sea",
    "lakshadweep sea":    "lakshadweep",
}


def region_to_bbox(region: str) -> Optional[tuple[float, float, float, float]]:
    """Return (lat_min, lat_max, lon_min, lon_max) for a named region, or None."""
    key = ALIASES.get(region.lower(), region.lower().replace(" ", "_"))
    return REGION_BOUNDS.get(key)


def bbox_sql_filter(
    lat_min: float, lat_max: float, lon_min: float, lon_max: float,
    lat_col: str = "lat", lon_col: str = "lon",
) -> str:
    """Return a SQL WHERE snippet for a bounding-box filter."""
    return (
        f"{lat_col} BETWEEN {lat_min} AND {lat_max} "
        f"AND {lon_col} BETWEEN {lon_min} AND {lon_max}"
    )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two points."""
    import math

    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def make_geojson_point(lat: float, lon: float, properties: dict | None = None) -> dict:
    """Construct a minimal GeoJSON Feature (Point)."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties or {},
    }
