-- Runs automatically on first Postgres container start (mounted into
-- /docker-entrypoint-initdb.d/). SQLAlchemy's init_db() also creates
-- tables via ORM metadata, so this file mainly guarantees extensions
-- exist and adds a couple of query-pattern indexes SQLAlchemy doesn't
-- express well (e.g. spatial GIST indexes).

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector; requires the pgvector/pgvector-postgis image

-- Tables themselves are created by backend/database.py::init_db() via
-- SQLAlchemy metadata (see backend/models/). If you need to run this
-- SQL standalone (no ORM available), uncomment the CREATE TABLE block
-- below — kept in sync manually with backend/models/*.py.

-- CREATE TABLE IF NOT EXISTS float_metadata (
--     id SERIAL PRIMARY KEY,
--     wmo_id VARCHAR(16) UNIQUE NOT NULL,
--     dac VARCHAR(32),
--     platform_type VARCHAR(64),
--     project_name VARCHAR(128),
--     pi_name VARCHAR(128),
--     deploy_date DATE,
--     deploy_lat DOUBLE PRECISION,
--     deploy_lon DOUBLE PRECISION,
--     is_bgc BOOLEAN DEFAULT FALSE,
--     status VARCHAR(16) DEFAULT 'active'
-- );
--
-- CREATE TABLE IF NOT EXISTS profiles (
--     id SERIAL PRIMARY KEY,
--     float_id INTEGER REFERENCES float_metadata(id),
--     cycle_number INTEGER NOT NULL,
--     "timestamp" TIMESTAMP NOT NULL,
--     lat DOUBLE PRECISION NOT NULL,
--     lon DOUBLE PRECISION NOT NULL,
--     geom geometry(Point, 4326),
--     pressure DOUBLE PRECISION NOT NULL,
--     temperature DOUBLE PRECISION,
--     salinity DOUBLE PRECISION,
--     pressure_qc VARCHAR(2),
--     temperature_qc VARCHAR(2),
--     salinity_qc VARCHAR(2)
-- );
--
-- CREATE TABLE IF NOT EXISTS trajectory_points (
--     id SERIAL PRIMARY KEY,
--     float_id INTEGER REFERENCES float_metadata(id),
--     cycle_number INTEGER NOT NULL,
--     "timestamp" TIMESTAMP NOT NULL,
--     lat DOUBLE PRECISION NOT NULL,
--     lon DOUBLE PRECISION NOT NULL,
--     geom geometry(Point, 4326),
--     predicted_next_lat DOUBLE PRECISION,
--     predicted_next_lon DOUBLE PRECISION,
--     prediction_confidence DOUBLE PRECISION,
--     UNIQUE (float_id, cycle_number)
-- );
--
-- CREATE TABLE IF NOT EXISTS bgc_profiles (
--     id SERIAL PRIMARY KEY,
--     float_id INTEGER REFERENCES float_metadata(id),
--     cycle_number INTEGER NOT NULL,
--     "timestamp" TIMESTAMP NOT NULL,
--     lat DOUBLE PRECISION NOT NULL,
--     lon DOUBLE PRECISION NOT NULL,
--     pressure DOUBLE PRECISION NOT NULL,
--     dissolved_oxygen DOUBLE PRECISION,
--     chlorophyll DOUBLE PRECISION,
--     ph DOUBLE PRECISION,
--     nitrate DOUBLE PRECISION,
--     backscatter DOUBLE PRECISION,
--     dissolved_oxygen_qc VARCHAR(2),
--     chlorophyll_qc VARCHAR(2),
--     ph_qc VARCHAR(2),
--     nitrate_qc VARCHAR(2)
-- );

-- Query-pattern indexes (region + date, float_id, depth range)
CREATE INDEX IF NOT EXISTS ix_profiles_geom ON profiles USING GIST (geom);
CREATE INDEX IF NOT EXISTS ix_traj_geom ON trajectory_points USING GIST (geom);
CREATE INDEX IF NOT EXISTS ix_profiles_pressure ON profiles (pressure);
CREATE INDEX IF NOT EXISTS ix_bgc_pressure ON bgc_profiles (pressure);

-- Read-only role for LLM-generated SQL (see backend/nl2sql/sql_validator.py).
-- Password should be overridden in production via env/secrets, not left here.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'floatchat_readonly') THEN
        CREATE ROLE floatchat_readonly WITH LOGIN PASSWORD 'change_me_readonly';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE floatchat TO floatchat_readonly;
GRANT USAGE ON SCHEMA public TO floatchat_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO floatchat_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO floatchat_readonly;