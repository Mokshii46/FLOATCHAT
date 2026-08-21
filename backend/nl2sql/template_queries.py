"""
Hardcoded, parameterized SQL templates for the question types we expect
most often. These are matched first (see router.py) because they're fast,
deterministic, and can't hallucinate a bad column name — freeform NL2SQL
(query_generator.py) is only used when nothing here fits.

Every template:
  - is a plain string with SQLAlchemy-style named bind params (`:param`)
  - only ever SELECTs (still re-checked by sql_validator.py before execution)
  - includes its own LIMIT, but sql_validator.py enforces a hard cap anyway

`required_params` lists the bind params router.py MUST have extracted from
the question for this template to be usable; if any are missing, router.py
falls back to freeform NL2SQL instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Template:
    key: str
    description: str
    sql: str
    required_params: list[str]
    keywords: list[str]  # used by router.py's keyword scoring


TEMPLATES: dict[str, Template] = {}


def _register(t: Template) -> None:
    TEMPLATES[t.key] = t


# 1. Avg temperature/salinity in a region + date range, at ~a given depth
_register(
    Template(
        key="avg_var_region_depth",
        description="Average temperature/salinity in a region and date range, near a given pressure/depth.",
        sql="""
            SELECT date_trunc('month', p.timestamp) AS month,
                   AVG(p.temperature) AS avg_temperature,
                   AVG(p.salinity) AS avg_salinity,
                   COUNT(*) AS n_obs
            FROM profiles p
            WHERE p.lon BETWEEN :lon_min AND :lon_max
              AND p.lat BETWEEN :lat_min AND :lat_max
              AND p.timestamp BETWEEN :start_date AND :end_date
              AND p.pressure BETWEEN :pressure_min AND :pressure_max
            GROUP BY 1
            ORDER BY 1
            LIMIT :row_limit
        """,
        required_params=["lon_min", "lon_max", "lat_min", "lat_max", "start_date", "end_date", "pressure_min", "pressure_max"],
        keywords=["average", "mean", "temperature", "salinity", "region", "depth"],
    )
)

# 2. Trend over time in a region (no depth filter — surface-ish default)
_register(
    Template(
        key="trend_region",
        description="Monthly temperature/salinity trend in a region over a date range.",
        sql="""
            SELECT date_trunc('month', p.timestamp) AS month,
                   AVG(p.temperature) AS avg_temperature,
                   AVG(p.salinity) AS avg_salinity
            FROM profiles p
            WHERE p.lon BETWEEN :lon_min AND :lon_max
              AND p.lat BETWEEN :lat_min AND :lat_max
              AND p.timestamp BETWEEN :start_date AND :end_date
              AND p.pressure <= :pressure_max
            GROUP BY 1
            ORDER BY 1
            LIMIT :row_limit
        """,
        required_params=["lon_min", "lon_max", "lat_min", "lat_max", "start_date", "end_date", "pressure_max"],
        keywords=["trend", "over time", "warming", "cooling", "change", "region"],
    )
)

# 3. Compare two named floats (by wmo_id)
_register(
    Template(
        key="compare_floats",
        description="Compare temperature/salinity profiles between two specific floats.",
        sql="""
            SELECT fm.wmo_id, p.cycle_number, p.pressure, p.temperature, p.salinity, p.timestamp
            FROM profiles p
            JOIN float_metadata fm ON fm.id = p.float_id
            WHERE fm.wmo_id IN (:wmo_id_a, :wmo_id_b)
            ORDER BY fm.wmo_id, p.cycle_number, p.pressure
            LIMIT :row_limit
        """,
        required_params=["wmo_id_a", "wmo_id_b"],
        keywords=["compare", "vs", "versus", "float", "floats"],
    )
)

# 4. Single float's full depth profile for its latest cycle
_register(
    Template(
        key="float_latest_profile",
        description="Depth profile (temperature/salinity vs pressure) for a float's most recent cycle.",
        sql="""
            SELECT p.pressure, p.temperature, p.salinity, p.timestamp
            FROM profiles p
            JOIN float_metadata fm ON fm.id = p.float_id
            WHERE fm.wmo_id = :wmo_id
              AND p.cycle_number = (
                  SELECT MAX(cycle_number) FROM profiles p2
                  JOIN float_metadata fm2 ON fm2.id = p2.float_id
                  WHERE fm2.wmo_id = :wmo_id
              )
            ORDER BY p.pressure
            LIMIT :row_limit
        """,
        required_params=["wmo_id"],
        keywords=["profile", "depth", "latest", "recent", "float"],
    )
)

# 5. Where is a float right now (most recent surfacing position)
_register(
    Template(
        key="float_current_position",
        description="Most recent known surfacing position of a float, plus predicted next position if available.",
        sql="""
            SELECT fm.wmo_id, tp.timestamp, tp.lat, tp.lon,
                   tp.predicted_next_lat, tp.predicted_next_lon, tp.prediction_confidence
            FROM trajectory_points tp
            JOIN float_metadata fm ON fm.id = tp.float_id
            WHERE fm.wmo_id = :wmo_id
            ORDER BY tp.timestamp DESC
            LIMIT 1
        """,
        required_params=["wmo_id"],
        keywords=["where", "current", "position", "location", "now", "float"],
    )
)

# 6. Full trajectory (path) of a float
_register(
    Template(
        key="float_trajectory",
        description="Full surfacing-position history of a float, ordered by time.",
        sql="""
            SELECT tp.cycle_number, tp.timestamp, tp.lat, tp.lon
            FROM trajectory_points tp
            JOIN float_metadata fm ON fm.id = tp.float_id
            WHERE fm.wmo_id = :wmo_id
            ORDER BY tp.cycle_number
            LIMIT :row_limit
        """,
        required_params=["wmo_id"],
        keywords=["path", "trajectory", "route", "track", "float"],
    )
)

# 7. Count / list floats in a region
_register(
    Template(
        key="floats_in_region",
        description="Floats whose most recent known position falls inside a region.",
        sql="""
            SELECT DISTINCT ON (fm.wmo_id) fm.wmo_id, fm.platform_type, fm.is_bgc, tp.timestamp, tp.lat, tp.lon
            FROM trajectory_points tp
            JOIN float_metadata fm ON fm.id = tp.float_id
            WHERE tp.lon BETWEEN :lon_min AND :lon_max
              AND tp.lat BETWEEN :lat_min AND :lat_max
            ORDER BY fm.wmo_id, tp.timestamp DESC
            LIMIT :row_limit
        """,
        required_params=["lon_min", "lon_max", "lat_min", "lat_max"],
        keywords=["how many", "floats", "region", "in the", "near"],
    )
)

# 8. BGC variable in a region (USP 7)
_register(
    Template(
        key="bgc_region",
        description="Average BGC variable (oxygen/chlorophyll/pH/nitrate) in a region and date range.",
        sql="""
            SELECT date_trunc('month', b.timestamp) AS month,
                   AVG(b.dissolved_oxygen) AS avg_oxygen,
                   AVG(b.chlorophyll) AS avg_chlorophyll,
                   AVG(b.ph) AS avg_ph,
                   AVG(b.nitrate) AS avg_nitrate,
                   COUNT(*) AS n_obs
            FROM bgc_profiles b
            WHERE b.lon BETWEEN :lon_min AND :lon_max
              AND b.lat BETWEEN :lat_min AND :lat_max
              AND b.timestamp BETWEEN :start_date AND :end_date
            GROUP BY 1
            ORDER BY 1
            LIMIT :row_limit
        """,
        required_params=["lon_min", "lon_max", "lat_min", "lat_max", "start_date", "end_date"],
        keywords=["oxygen", "chlorophyll", "ph", "nitrate", "bgc", "biogeochemical"],
    )
)

# 9. Deepest / shallowest reading for a float
_register(
    Template(
        key="float_extreme_depth",
        description="Deepest (max pressure) profile reading recorded by a float.",
        sql="""
            SELECT p.cycle_number, p.pressure, p.temperature, p.salinity, p.timestamp
            FROM profiles p
            JOIN float_metadata fm ON fm.id = p.float_id
            WHERE fm.wmo_id = :wmo_id
            ORDER BY p.pressure DESC
            LIMIT :row_limit
        """,
        required_params=["wmo_id"],
        keywords=["deepest", "maximum depth", "float"],
    )
)

# 10. List/count BGC floats (metadata only, no measurement filter)
_register(
    Template(
        key="list_bgc_floats",
        description="List all floats flagged as BGC-equipped, optionally filtered by DAC.",
        sql="""
            SELECT wmo_id, dac, platform_type, project_name, status
            FROM float_metadata
            WHERE is_bgc = TRUE
            ORDER BY wmo_id
            LIMIT :row_limit
        """,
        required_params=[],
        keywords=["bgc floats", "list floats", "which floats", "biogeochemical floats"],
    )
)

# 11. Float metadata lookup (who deployed it, when, platform type)
_register(
    Template(
        key="float_metadata_lookup",
        description="Metadata for a single float: PI, project, deploy date/location, platform type.",
        sql="""
            SELECT wmo_id, dac, platform_type, project_name, pi_name,
                   deploy_date, deploy_lat, deploy_lon, is_bgc, status
            FROM float_metadata
            WHERE wmo_id = :wmo_id
        """,
        required_params=["wmo_id"],
        keywords=["who deployed", "when was", "pi", "project", "float"],
    )
)

# 12. Active vs dead float counts
_register(
    Template(
        key="float_status_counts",
        description="Count of floats by status (active/dead/unknown).",
        sql="""
            SELECT status, COUNT(*) AS n_floats
            FROM float_metadata
            GROUP BY status
            ORDER BY n_floats DESC
        """,
        required_params=[],
        keywords=["how many floats", "active floats", "dead floats", "status"],
    )
)

# 13. Salinity/temperature at surface (shallow) in a region, single snapshot
_register(
    Template(
        key="surface_snapshot_region",
        description="Most recent surface-level (pressure < 20 dbar) readings in a region.",
        sql="""
            SELECT fm.wmo_id, p.timestamp, p.lat, p.lon, p.pressure, p.temperature, p.salinity
            FROM profiles p
            JOIN float_metadata fm ON fm.id = p.float_id
            WHERE p.lon BETWEEN :lon_min AND :lon_max
              AND p.lat BETWEEN :lat_min AND :lat_max
              AND p.pressure < 20
            ORDER BY p.timestamp DESC
            LIMIT :row_limit
        """,
        required_params=["lon_min", "lon_max", "lat_min", "lat_max"],
        keywords=["surface", "sea surface", "region", "current"],
    )
)

# 14. Cycles per float (data density check)
_register(
    Template(
        key="float_cycle_count",
        description="Number of cycles recorded for a float — useful for 'how much data do we have'.",
        sql="""
            SELECT fm.wmo_id, COUNT(DISTINCT p.cycle_number) AS n_cycles,
                   MIN(p.timestamp) AS first_cycle, MAX(p.timestamp) AS last_cycle
            FROM profiles p
            JOIN float_metadata fm ON fm.id = p.float_id
            WHERE fm.wmo_id = :wmo_id
            GROUP BY fm.wmo_id
        """,
        required_params=["wmo_id"],
        keywords=["how many cycles", "how much data", "float"],
    )
)

# 15. Anomalous readings — simple threshold-based outlier scan in a region (feeds USP 1's raw data)
_register(
    Template(
        key="temperature_outliers_region",
        description="Profile rows in a region/date range whose temperature is furthest from the region's mean (candidate anomalies).",
        sql="""
            WITH stats AS (
                SELECT AVG(temperature) AS mean_t, STDDEV(temperature) AS std_t
                FROM profiles
                WHERE lon BETWEEN :lon_min AND :lon_max
                  AND lat BETWEEN :lat_min AND :lat_max
                  AND timestamp BETWEEN :start_date AND :end_date
            )
            SELECT p.timestamp, p.lat, p.lon, p.pressure, p.temperature,
                   ABS(p.temperature - stats.mean_t) / NULLIF(stats.std_t, 0) AS z_score
            FROM profiles p, stats
            WHERE p.lon BETWEEN :lon_min AND :lon_max
              AND p.lat BETWEEN :lat_min AND :lat_max
              AND p.timestamp BETWEEN :start_date AND :end_date
              AND p.temperature IS NOT NULL
            ORDER BY z_score DESC NULLS LAST
            LIMIT :row_limit
        """,
        required_params=["lon_min", "lon_max", "lat_min", "lat_max", "start_date", "end_date"],
        keywords=["anomaly", "anomalous", "unusual", "outlier", "spike"],
    )
)


def render(key: str, params: dict) -> str:
    """Returns the raw SQL string for a template (bind params substituted by the DB driver, not here)."""
    return TEMPLATES[key].sql


def get_template(key: str) -> Template | None:
    return TEMPLATES.get(key)