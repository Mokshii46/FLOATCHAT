# FloatChat Database Schema

## Tables

### `float_metadata`
Primary registry of ARGO floats.

```sql
CREATE TABLE float_metadata (
    id            SERIAL PRIMARY KEY,
    wmo_id        VARCHAR(16)  NOT NULL UNIQUE,
    dac           VARCHAR(32),
    platform_type VARCHAR(64),
    project_name  VARCHAR(128),
    pi_name       VARCHAR(128),
    deploy_date   DATE,
    deploy_lat    FLOAT,
    deploy_lon    FLOAT,
    is_bgc        BOOLEAN DEFAULT FALSE,
    status        VARCHAR(16)  DEFAULT 'active'
);
```

### `profiles`
One row per (float, cycle, pressure level) — core T/S data.

```sql
CREATE TABLE profiles (
    id              SERIAL PRIMARY KEY,
    float_id        INTEGER NOT NULL REFERENCES float_metadata(id),
    cycle_number    INTEGER NOT NULL,
    timestamp       TIMESTAMP,
    lat             FLOAT,
    lon             FLOAT,
    geom            GEOMETRY(POINT, 4326),
    pressure        FLOAT,
    temperature     FLOAT,
    salinity        FLOAT,
    pressure_qc     VARCHAR(2),
    temperature_qc  VARCHAR(2),
    salinity_qc     VARCHAR(2)
);
```

### `trajectory_points`
One row per cycle surfacing (lightweight, map-optimised).

```sql
CREATE TABLE trajectory_points (
    id                    SERIAL PRIMARY KEY,
    float_id              INTEGER NOT NULL REFERENCES float_metadata(id),
    cycle_number          INTEGER NOT NULL,
    timestamp             TIMESTAMP,
    lat                   FLOAT,
    lon                   FLOAT,
    geom                  GEOMETRY(POINT, 4326),
    predicted_next_lat    FLOAT,
    predicted_next_lon    FLOAT,
    prediction_confidence FLOAT,
    UNIQUE (float_id, cycle_number)
);
```

### `bgc_profiles`
BGC (Bio-Geochemical) measurements — only for `is_bgc=true` floats.

```sql
CREATE TABLE bgc_profiles (
    id                   SERIAL PRIMARY KEY,
    float_id             INTEGER NOT NULL REFERENCES float_metadata(id),
    cycle_number         INTEGER NOT NULL,
    timestamp            TIMESTAMP,
    lat                  FLOAT,
    lon                  FLOAT,
    pressure             FLOAT,
    dissolved_oxygen     FLOAT,   -- µmol/kg
    chlorophyll          FLOAT,   -- mg/m³
    ph                   FLOAT,   -- total scale
    nitrate              FLOAT,   -- µmol/kg
    backscatter          FLOAT,   -- m⁻¹
    dissolved_oxygen_qc  VARCHAR(2),
    chlorophyll_qc       VARCHAR(2),
    ph_qc                VARCHAR(2),
    nitrate_qc           VARCHAR(2)
);
```

## Indexes

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| `ix_profiles_float_cycle` | profiles | float_id, cycle_number | Profile lookup by float+cycle |
| `ix_profiles_timestamp_pressure` | profiles | timestamp, pressure | Time+depth range queries |
| `ix_traj_float_cycle` | trajectory_points | float_id, cycle_number | Unique, fast trajectory fetch |
| `ix_profiles_geom` | profiles | geom (GIST) | Spatial proximity queries |
| `ix_traj_geom` | trajectory_points | geom (GIST) | Spatial map queries |
| `ix_bgc_float_cycle` | bgc_profiles | float_id, cycle_number | BGC profile fetch |

## Extensions Required
- `postgis` — spatial geometry types and GIST indexes
- `postgis_topology` — optional topological operations
- `vector` (pgvector) — optional embedding storage if using Postgres as vector backend
