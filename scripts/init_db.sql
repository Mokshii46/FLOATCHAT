-- FloatChat database initialisation
-- Run automatically via Docker entrypoint or manually with:
--   psql -U floatchat -d floatchat -f init_db.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS vector;   -- pgvector (optional; we use ChromaDB by default)

-- Read-only role for NL2SQL query execution
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'floatchat_readonly') THEN
        CREATE ROLE floatchat_readonly LOGIN PASSWORD 'readonly_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE floatchat TO floatchat_readonly;
GRANT USAGE  ON SCHEMA public TO floatchat_readonly;

-- Grant SELECT on all existing + future tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO floatchat_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO floatchat_readonly;

-- ORM-managed tables (created by SQLAlchemy / init_db())
-- Listed here for documentation; SQLAlchemy will CREATE them.
-- float_metadata, profiles, trajectory_points, bgc_profiles

-- Spatial indexes (created alongside ORM tables, listed for clarity)
-- CREATE INDEX IF NOT EXISTS ix_profiles_geom ON profiles USING GIST (geom);
-- CREATE INDEX IF NOT EXISTS ix_traj_geom     ON trajectory_points USING GIST (geom);