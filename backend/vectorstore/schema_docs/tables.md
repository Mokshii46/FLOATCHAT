# FloatChat Database Schema Reference

This document describes every table and column in the FloatChat PostgreSQL database.
It is embedded into the vector store to ground the LLM's SQL generation.

---

## Table: `float_metadata`

One row per physical ARGO float.

| Column         | Type        | Description |
|----------------|-------------|-------------|
| id             | integer PK  | Internal surrogate key |
| wmo_id         | varchar(16) | WMO float identifier (e.g. "2902183") — unique |
| dac            | varchar(32) | Data Assembly Centre (e.g. "incois", "coriolis") |
| platform_type  | varchar(64) | Float model (e.g. "APEX", "NOVA", "ARVOR") |
| project_name   | varchar(128)| Research programme name |
| pi_name        | varchar(128)| Principal investigator |
| deploy_date    | date        | Date of float deployment |
| deploy_lat     | float       | Deployment latitude (degrees North) |
| deploy_lon     | float       | Deployment longitude (degrees East) |
| is_bgc         | boolean     | True if float carries BGC sensors |
| status         | varchar(16) | "active", "dead", or "unknown" |

---

## Table: `profiles`

One row per (float, cycle, pressure level) — the main physical oceanography table.

| Column          | Type        | Description |
|-----------------|-------------|-------------|
| id              | integer PK  | Surrogate key |
| float_id        | integer FK  | References float_metadata.id |
| cycle_number    | integer     | Argo cycle counter (ascent number) |
| timestamp       | datetime    | UTC time of observation |
| lat             | float       | Latitude (degrees North, –90 to 90) |
| lon             | float       | Longitude (degrees East, –180 to 180) |
| geom            | geometry    | PostGIS POINT(lon lat) SRID 4326 |
| pressure        | float       | Pressure in dbar (≈ depth in meters) |
| temperature     | float       | In-situ temperature, degrees Celsius |
| salinity        | float       | Practical salinity units (PSU) |
| pressure_qc     | varchar(2)  | Argo QC flag: 1=good, 2=probably good, 4=bad |
| temperature_qc  | varchar(2)  | Temperature QC flag |
| salinity_qc     | varchar(2)  | Salinity QC flag |

**Indexes**: float_id, timestamp, (float_id, cycle_number), (timestamp, pressure)

---

## Table: `trajectory_points`

One row per cycle surfacing event — lightweight position table for map rendering
and trajectory prediction (USP 3).

| Column                 | Type    | Description |
|------------------------|---------|-------------|
| id                     | integer | Surrogate key |
| float_id               | integer | FK → float_metadata.id |
| cycle_number           | integer | Argo cycle number |
| timestamp              | datetime| UTC surfacing time |
| lat                    | float   | Surfacing latitude |
| lon                    | float   | Surfacing longitude |
| geom                   | geometry| PostGIS POINT |
| predicted_next_lat     | float   | ML-predicted next surfacing lat (nullable) |
| predicted_next_lon     | float   | ML-predicted next surfacing lon (nullable) |
| prediction_confidence  | float   | Model confidence 0–1 (nullable) |

---

## Table: `bgc_profiles`

BGC (Bio-Geochemical) Argo measurements. Only populated when `float_metadata.is_bgc = true`.
Sourced from `*_Sprof.nc` files. Backs USP 7.

| Column               | Type    | Description |
|----------------------|---------|-------------|
| id                   | integer | Surrogate key |
| float_id             | integer | FK → float_metadata.id |
| cycle_number         | integer | Argo cycle number |
| timestamp            | datetime| UTC time |
| lat / lon            | float   | Position |
| pressure             | float   | Pressure in dbar |
| dissolved_oxygen     | float   | Dissolved oxygen, µmol/kg |
| chlorophyll          | float   | Chlorophyll-a concentration, mg/m³ |
| ph                   | float   | pH (total scale) |
| nitrate              | float   | Nitrate, µmol/kg |
| backscatter          | float   | Particulate backscattering coefficient 700nm, m⁻¹ |
| *_qc fields          | varchar | Argo QC flags for each BGC parameter |

---

## Common Query Patterns

- Filter by region: `WHERE lat BETWEEN {lat_min} AND {lat_max} AND lon BETWEEN {lon_min} AND {lon_max}`
- Filter by depth: `WHERE pressure BETWEEN {p_min} AND {p_max}`
- Filter by date: `WHERE timestamp BETWEEN '{date_start}' AND '{date_end}'`
- Join float name: `JOIN float_metadata fm ON p.float_id = fm.id WHERE fm.wmo_id = '{wmo}'`
- Always add `LIMIT 5000` to prevent runaway result sets.
- Use `AVG()`, `MIN()`, `MAX()` with `GROUP BY` for aggregations.
