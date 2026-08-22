"""
~15 hardcoded SQL templates for the most common ARGO question types.

Each template is a dict with:
  - keywords : list of trigger keyword sets (any set fully matching → route here)
  - sql       : parameterised SQL using Python str.format() placeholders
  - params    : list of required parameter names
  - description : human-readable label (shown in ExplainabilityPanel)

NOTE: All SQL is written in SQLite-compatible dialect (strftime instead of
DATE_TRUNC, CAST instead of ::numeric, datetime('now') instead of NOW()).
"""

from __future__ import annotations

TEMPLATES: list[dict] = [

    # 1. Average SST in a region
    {
        "id": "avg_sst_region",
        "description": "Average sea surface temperature in a geographic region",
        "keywords": [{"temperature", "average", "region"}, {"sst", "region"},
                     {"temperature", "mean"}, {"temperature", "sea"},
                     {"temperature", "arabian"}, {"temperature", "bengal"},
                     {"temperature", "ocean"}, {"temperature", "year"},
                     {"temperature", "indian"}],
        "sql": """
SELECT
    strftime('%Y-%m', timestamp) AS month,
    ROUND(AVG(temperature), 3) AS avg_temp_c,
    COUNT(*) AS n_obs
FROM profiles
WHERE lat BETWEEN {lat_min} AND {lat_max}
  AND lon BETWEEN {lon_min} AND {lon_max}
  AND pressure BETWEEN 0 AND 10
  AND timestamp BETWEEN '{date_start}' AND '{date_end}'
GROUP BY month
ORDER BY month
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max", "date_start", "date_end"],
    },

    # 2. Salinity in a region over time
    {
        "id": "salinity_region",
        "description": "Average salinity in a geographic region over time",
        "keywords": [{"salinity", "region"}, {"salinity", "ocean"},
                     {"salinity", "sea"}, {"salinity", "bay"}, {"salinity", "gulf"},
                     {"salinity", "arabian"}, {"salinity", "bengal"},
                     {"salinity", "indian"}],
        "sql": """
SELECT
    strftime('%Y-%m', timestamp) AS month,
    ROUND(AVG(salinity), 4) AS avg_salinity_psu,
    COUNT(*) AS n_obs
FROM profiles
WHERE lat BETWEEN {lat_min} AND {lat_max}
  AND lon BETWEEN {lon_min} AND {lon_max}
  AND timestamp BETWEEN '{date_start}' AND '{date_end}'
GROUP BY month
ORDER BY month
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max", "date_start", "date_end"],
    },

    # 3. Float trajectory
    {
        "id": "float_trajectory",
        "description": "Surfacing path of a specific float",
        "keywords": [{"trajectory", "float"}, {"path", "float"}, {"track", "float"},
                     {"position", "float"}, {"movement", "float"}],
        "sql": """
SELECT tp.cycle_number, tp.timestamp, tp.lat, tp.lon,
       tp.predicted_next_lat, tp.predicted_next_lon
FROM trajectory_points tp
JOIN float_metadata fm ON tp.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
ORDER BY tp.cycle_number
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },

    # 4. Depth profile (T/S vs pressure) for a float cycle
    {
        "id": "depth_profile",
        "description": "Temperature/salinity vs depth for a specific float and cycle",
        "keywords": [{"depth", "profile"}, {"pressure", "temperature"},
                     {"profile", "float"}, {"depth", "float"}],
        "sql": """
SELECT p.pressure, p.temperature, p.salinity,
       p.temperature_qc, p.salinity_qc, p.timestamp
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND p.cycle_number = {cycle_number}
ORDER BY p.pressure
LIMIT 5000;
""",
        "params": ["wmo_id", "cycle_number"],
    },

    # 5. Compare two floats
    {
        "id": "compare_floats",
        "description": "Mean temperature vs depth for two floats",
        "keywords": [{"compare", "float"}, {"compare", "wmo"},
                     {"difference", "float"}, {"versus", "float"}],
        "sql": """
SELECT fm.wmo_id,
       CAST(ROUND(p.pressure / 100) * 100 AS INTEGER) AS pressure_bin,
       ROUND(AVG(p.temperature), 3) AS avg_temp,
       ROUND(AVG(p.salinity), 4) AS avg_sal
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
WHERE fm.wmo_id IN ('{wmo_id_1}', '{wmo_id_2}')
GROUP BY fm.wmo_id, pressure_bin
ORDER BY fm.wmo_id, pressure_bin
LIMIT 5000;
""",
        "params": ["wmo_id_1", "wmo_id_2"],
    },

    # 6. List active floats
    {
        "id": "list_active_floats",
        "description": "List of all active floats",
        "keywords": [{"list", "float"}, {"active", "float"}, {"all", "float"},
                     {"floats", "active"}, {"available", "float"},
                     {"show", "float"}, {"show", "active"}, {"how", "many", "float"}],
        "sql": """
SELECT wmo_id, dac, platform_type, deploy_date,
       deploy_lat, deploy_lon, is_bgc, status
FROM float_metadata
WHERE status = 'active'
ORDER BY deploy_date DESC
LIMIT 5000;
""",
        "params": [],
    },

    # 7. BGC — chlorophyll profile
    {
        "id": "chlorophyll_profile",
        "description": "Chlorophyll-a concentration vs depth for a BGC float",
        "keywords": [{"chlorophyll", "depth"}, {"chlorophyll", "profile"},
                     {"chla", "depth"}, {"algae", "depth"}],
        "sql": """
SELECT b.pressure, b.chlorophyll, b.chlorophyll_qc,
       b.timestamp, b.lat, b.lon
FROM bgc_profiles b
JOIN float_metadata fm ON b.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND b.chlorophyll IS NOT NULL
ORDER BY b.pressure
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },

    # 8. BGC — dissolved oxygen trend
    {
        "id": "oxygen_trend",
        "description": "Dissolved oxygen trend at a depth range in a region",
        "keywords": [{"oxygen", "trend"}, {"dissolved", "oxygen"},
                     {"o2", "depth"}, {"hypoxia"}],
        "sql": """
SELECT strftime('%Y-%m', b.timestamp) AS month,
       AVG(b.dissolved_oxygen) AS avg_oxygen_umolkg
FROM bgc_profiles b
WHERE b.lat BETWEEN {lat_min} AND {lat_max}
  AND b.lon BETWEEN {lon_min} AND {lon_max}
  AND b.pressure BETWEEN {p_min} AND {p_max}
GROUP BY month
ORDER BY month
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max", "p_min", "p_max"],
    },

    # 9. BGC — list BGC floats
    {
        "id": "list_bgc_floats",
        "description": "List all active BGC floats",
        "keywords": [{"bgc", "float"}, {"biogeochemical"}, {"bgc", "list"},
                     {"oxygen", "float"}, {"chlorophyll", "float"},
                     {"show", "bgc"}, {"bgc", "map"}],
        "sql": """
SELECT wmo_id, dac, platform_type, deploy_date,
       deploy_lat, deploy_lon
FROM float_metadata
WHERE is_bgc = 1 AND status = 'active'
ORDER BY deploy_date DESC
LIMIT 5000;
""",
        "params": [],
    },

    # 10. Temperature anomaly vs long-term mean
    {
        "id": "temp_anomaly",
        "description": "Monthly temperature anomaly relative to long-term mean",
        "keywords": [{"anomaly", "temperature"}, {"warming", "trend"},
                     {"temperature", "change"}, {"heat", "anomaly"}],
        "sql": """
WITH monthly AS (
    SELECT strftime('%Y-%m', timestamp) AS month,
           ROUND(AVG(temperature), 3) AS avg_temp
    FROM profiles
    WHERE lat BETWEEN {lat_min} AND {lat_max}
      AND lon BETWEEN {lon_min} AND {lon_max}
      AND pressure BETWEEN 0 AND 10
    GROUP BY month
),
long_term AS (
    SELECT AVG(avg_temp) AS climatology FROM monthly
)
SELECT m.month,
       m.avg_temp,
       ROUND(m.avg_temp - lt.climatology, 3) AS anomaly
FROM monthly m, long_term lt
ORDER BY m.month
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max"],
    },

    # 11. Floats in a bounding box
    {
        "id": "floats_in_region",
        "description": "Floats observed in a geographic bounding box",
        "keywords": [{"float", "region"}, {"float", "area"}, {"float", "location"},
                     {"float", "bay"}, {"float", "arabian"}, {"float", "bengal"},
                     {"map", "float"}, {"map", "show"}],
        "sql": """
SELECT DISTINCT fm.wmo_id, fm.dac, fm.platform_type, fm.is_bgc,
       tp.lat, tp.lon, tp.timestamp
FROM trajectory_points tp
JOIN float_metadata fm ON tp.float_id = fm.id
WHERE tp.lat BETWEEN {lat_min} AND {lat_max}
  AND tp.lon BETWEEN {lon_min} AND {lon_max}
  AND tp.timestamp BETWEEN '{date_start}' AND '{date_end}'
ORDER BY tp.timestamp DESC
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max", "date_start", "date_end"],
    },

    # 12. Thermocline depth (max temperature gradient)
    {
        "id": "thermocline_depth",
        "description": "Approximate thermocline depth for a float cycle",
        "keywords": [{"thermocline"}, {"mixed layer"}, {"mld"}, {"thermocline", "depth"}],
        "sql": """
SELECT sub.pressure AS thermocline_depth_dbar
FROM (
    SELECT pressure, temperature,
           temperature - LAG(temperature) OVER (ORDER BY pressure) AS dt
    FROM profiles p
    JOIN float_metadata fm ON p.float_id = fm.id
    WHERE fm.wmo_id = '{wmo_id}'
      AND p.cycle_number = {cycle_number}
      AND p.temperature IS NOT NULL
    ORDER BY pressure
) sub
ORDER BY ABS(sub.dt) DESC
LIMIT 1;
""",
        "params": ["wmo_id", "cycle_number"],
    },

    # 13. Float summary (latest cycle)
    {
        "id": "float_summary",
        "description": "Latest cycle summary for a specific float",
        "keywords": [{"float", "summary"}, {"float", "latest"}, {"float", "last"},
                     {"float", "recent"}, {"float", "current"}, {"float", "info"},
                     {"float", "details"}, {"float", "status"}],
        "sql": """
SELECT fm.wmo_id, fm.dac, fm.platform_type, fm.status,
       tp.cycle_number, tp.timestamp, tp.lat, tp.lon,
       tp.predicted_next_lat, tp.predicted_next_lon
FROM trajectory_points tp
JOIN float_metadata fm ON tp.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
ORDER BY tp.cycle_number DESC
LIMIT 1;
""",
        "params": ["wmo_id"],
    },

    # 14. Nitrate profile (BGC)
    {
        "id": "nitrate_profile",
        "description": "Nitrate concentration vs depth for a BGC float",
        "keywords": [{"nitrate", "depth"}, {"nitrate", "profile"}, {"no3", "depth"}],
        "sql": """
SELECT b.pressure, b.nitrate, b.nitrate_qc
FROM bgc_profiles b
JOIN float_metadata fm ON b.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND b.nitrate IS NOT NULL
ORDER BY b.pressure
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },

    # 15. pH profile (BGC)
    {
        "id": "ph_profile",
        "description": "pH vs depth for a BGC float",
        "keywords": [{"ph", "depth"}, {"ph", "profile"}, {"acidification"}],
        "sql": """
SELECT b.pressure, b.ph, b.ph_qc, b.timestamp
FROM bgc_profiles b
JOIN float_metadata fm ON b.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND b.ph IS NOT NULL
ORDER BY b.pressure
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },
]