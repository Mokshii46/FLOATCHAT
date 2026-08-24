"""
~18 hardcoded SQL templates for the most common ARGO question types.

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

    # 1. "Surprise me" — picks a random active float and summarizes its journey
    {
        "id": "surprise_float",
        "description": "Random active float journey and story",
        "keywords": [
            {"surprise"},
            {"surprise", "me"},
            {"random", "float"},
            {"random", "active"},
            {"pick", "random"},
            {"story", "float"},
        ],
        "sql": """
SELECT fm.wmo_id, fm.dac, fm.platform_type, fm.project_name, fm.pi_name,
       fm.is_bgc, fm.deploy_date, fm.deploy_lat, fm.deploy_lon,
       tp.cycle_number, tp.lat, tp.lon, tp.timestamp
FROM float_metadata fm
JOIN trajectory_points tp ON tp.float_id = fm.id
WHERE fm.status = 'active'
ORDER BY RANDOM()
LIMIT 1;
""",
        "params": [],
    },

    # 2. Average SST in a region
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
  AND pressure BETWEEN 0 AND 30
  AND timestamp BETWEEN '{date_start}' AND '{date_end}'
GROUP BY month
ORDER BY month
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max", "date_start", "date_end"],
    },

    # 3. Salinity in a region over time
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

    # 4. Compare two floats
    {
        "id": "compare_floats",
        "description": "Mean temperature vs depth for two floats",
        "keywords": [{"compare", "float"}, {"compare", "floats"}, {"compare", "wmo"},
                     {"compare"}, {"difference", "float"}, {"versus", "float"}],
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

    # 5. Thermocline depth (max temperature gradient) & MLD
    {
        "id": "thermocline_depth",
        "description": "Approximate thermocline depth and MLD for a float",
        "keywords": [{"thermocline"}, {"mld"}, {"mixed", "layer"},
                     {"thermocline", "mld"}, {"thermocline", "depth"},
                     {"thermocline", "float"}, {"mld", "float"}],
        "sql": """
SELECT sub.pressure AS thermocline_depth_dbar,
       ROUND(sub.dt, 3) AS max_temperature_gradient_c_per_dbar
FROM (
    SELECT p.pressure, p.temperature,
           p.temperature - LAG(p.temperature) OVER (ORDER BY p.pressure) AS dt
    FROM profiles p
    JOIN float_metadata fm ON p.float_id = fm.id
    WHERE fm.wmo_id = '{wmo_id}'
      AND p.temperature IS NOT NULL
    ORDER BY p.pressure
) sub
WHERE sub.dt IS NOT NULL
ORDER BY ABS(sub.dt) DESC
LIMIT 1;
""",
        "params": ["wmo_id"],
    },

    # 6. Depth profile (T/S vs pressure) with QC flags
    {
        "id": "depth_profile",
        "description": "Temperature/salinity vs depth for a specific float",
        "keywords": [{"depth", "profile"}, {"pressure", "temperature"},
                     {"profile", "float"}, {"depth", "float"},
                     {"flags", "float"}, {"qc", "float"}, {"raw", "float"},
                     {"profiles", "flags"}],
        "sql": """
SELECT p.pressure, p.temperature, p.salinity,
       p.temperature_qc, p.salinity_qc, p.timestamp
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
ORDER BY p.pressure
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },

    # 7. Float trajectory
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

    # 8. List active floats
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

    # 9. List BGC floats
    {
        "id": "list_bgc_floats",
        "description": "List of all active BioGeoChemical (BGC) ARGO floats",
        "keywords": [{"bgc", "float"}, {"biogeochemical", "float"}, {"oxygen", "float"},
                     {"chlorophyll", "float"}, {"sensors", "float"}],
        "sql": """
SELECT wmo_id, dac, platform_type, deploy_date,
       deploy_lat, deploy_lon, status
FROM float_metadata
WHERE is_bgc = 1 AND status = 'active'
ORDER BY deploy_date DESC
LIMIT 5000;
""",
        "params": [],
    },

    # 10. Deepest profile by float
    {
        "id": "deepest_profile",
        "description": "Maximum depth reached by each float",
        "keywords": [{"deepest", "float"}, {"maximum", "depth"}, {"max", "pressure"},
                     {"depth", "record"}],
        "sql": """
SELECT fm.wmo_id,
       ROUND(MAX(p.pressure), 1) AS max_pressure_dbar,
       COUNT(DISTINCT p.cycle_number) AS total_cycles
FROM profiles p
JOIN float_metadata fm ON p.float_id = fm.id
GROUP BY fm.wmo_id
ORDER BY max_pressure_dbar DESC
LIMIT 20;
""",
        "params": [],
    },

    # 11. BGC Dissolved Oxygen profile
    {
        "id": "bgc_doxy_profile",
        "description": "Dissolved oxygen vs depth for a BGC float",
        "keywords": [{"dissolved", "oxygen"}, {"oxygen", "profile"}, {"doxy", "profile"},
                     {"oxygen", "depth"}],
        "sql": """
SELECT bgc.pressure, bgc.doxy, bgc.doxy_qc, bgc.timestamp
FROM bgc_profiles bgc
JOIN float_metadata fm ON bgc.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND bgc.doxy IS NOT NULL
ORDER BY bgc.pressure
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },

    # 12. BGC Chlorophyll profile
    {
        "id": "bgc_chla_profile",
        "description": "Chlorophyll-A vs depth for a BGC float",
        "keywords": [{"chlorophyll", "profile"}, {"chla", "profile"}, {"chlorophyll", "depth"}],
        "sql": """
SELECT bgc.pressure, bgc.chla, bgc.chla_qc, bgc.timestamp
FROM bgc_profiles bgc
JOIN float_metadata fm ON bgc.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
  AND bgc.chla IS NOT NULL
ORDER BY bgc.pressure
LIMIT 5000;
""",
        "params": ["wmo_id"],
    },

    # 13. Regional float positions
    {
        "id": "regional_float_positions",
        "description": "Recent float surfacing positions in a geographic region",
        "keywords": [{"floats", "in"}, {"floats", "near"}, {"where", "floats"},
                     {"positions", "in"}, {"active", "in"}, {"which", "floats"}],
        "sql": """
SELECT fm.wmo_id, fm.is_bgc, fm.dac,
       tp.lat, tp.lon, tp.timestamp, tp.cycle_number
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

    # 14. Float summary
    {
        "id": "float_summary",
        "description": "Summary for a specific float",
        "keywords": [{"float", "summary"}, {"float", "latest"}, {"float", "last"},
                     {"float", "recent"}, {"float", "current"}, {"float", "info"},
                     {"float", "details"}, {"float", "status"}, {"tell", "float"}],
        "sql": """
SELECT fm.wmo_id, fm.dac, fm.platform_type, fm.project_name, fm.pi_name,
       fm.is_bgc, fm.deploy_date, fm.status,
       tp.cycle_number AS last_cycle, tp.lat AS last_lat, tp.lon AS last_lon,
       tp.timestamp AS last_surfacing
FROM float_metadata fm
JOIN trajectory_points tp ON tp.float_id = fm.id
WHERE fm.wmo_id = '{wmo_id}'
ORDER BY tp.cycle_number DESC
LIMIT 1;
""",
        "params": ["wmo_id"],
    },

    # 15. Ocean data near lat, lon
    {
        "id": "nearby_data",
        "description": "Recent ocean observations near a geographic coordinate",
        "keywords": [{"near", "latitude"}, {"near", "location"}, {"data", "near"},
                     {"ocean", "near"}, {"recent", "near"}],
        "sql": """
SELECT strftime('%Y-%m', timestamp) AS month,
       ROUND(AVG(temperature), 3) AS avg_temp_c,
       ROUND(AVG(salinity), 4) AS avg_salinity_psu,
       COUNT(*) AS n_obs
FROM profiles
WHERE lat BETWEEN {lat_min} AND {lat_max}
  AND lon BETWEEN {lon_min} AND {lon_max}
  AND pressure BETWEEN 0 AND 30
  AND timestamp >= datetime('now', '-1 years')
GROUP BY month
ORDER BY month
LIMIT 5000;
""",
        "params": ["lat_min", "lat_max", "lon_min", "lon_max"],
    },
]