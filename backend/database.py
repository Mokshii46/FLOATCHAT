"""
SQLAlchemy engine/session setup + PostGIS bootstrap with automatic SQLite fallback.
"""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent / "floatchat.db"

# ── Engine creation with automatic fallback ──────────────────────

def _create_engine():
    """Try PostgreSQL first, fall back to SQLite if connection fails."""
    db_url = settings.database_url
    if "postgresql" in db_url:
        try:
            pg_engine = create_engine(db_url, pool_pre_ping=True, future=True)
            # Actually test the connection
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL.")
            return pg_engine
        except Exception as exc:
            logger.warning(
                "PostgreSQL connection failed (%s). Falling back to SQLite at %s",
                exc, DB_PATH
            )

    sqlite_url = f"sqlite:///{DB_PATH}"
    return create_engine(sqlite_url, connect_args={"check_same_thread": False}, future=True)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

if "postgresql" in engine.dialect.name:
    from geoalchemy2 import Geometry
    SpatialPoint = Geometry(geometry_type="POINT", srid=4326)
else:
    from sqlalchemy import String
    SpatialPoint = String


def init_db() -> None:
    """Create database extensions/tables."""
    global engine, SessionLocal

    try:
        with engine.connect() as conn:
            if "postgresql" in engine.dialect.name:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                    conn.commit()
                except Exception as e:
                    logger.warning("Could not enable PostGIS extension: %s", e)
    except Exception as exc:
        logger.warning("Database connection error during init: %s", exc)
        # Force SQLite fallback
        engine = create_engine(
            f"sqlite:///{DB_PATH}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Import models so they register on Base.metadata before create_all
    try:
        from models import float_metadata, profile, trajectory, bgc_profile  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified using dialect: %s", engine.dialect.name)
    except Exception as exc:
        logger.error("Failed to create tables: %s", exc)


def get_db():
    """FastAPI dependency: yields a session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Use in scripts/ETL: `with session_scope() as db: ...` auto-commits/rolls back."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()