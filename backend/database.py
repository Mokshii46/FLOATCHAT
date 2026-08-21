"""
SQLAlchemy engine/session setup + PostGIS bootstrap.

Two DB roles are expected in production:
  - the "app" role used here (read/write, for ETL loads)
  - a separate read-only role used by nl2sql/sql_validator.py for
    executing LLM-generated SQL safely (never the app role).
"""

from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def init_db() -> None:
    """Create PostGIS extension (idempotent) and all ORM tables."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    # Import models so they register on Base.metadata before create_all
    from models import float_metadata, profile, trajectory, bgc_profile  # noqa: F401

    Base.metadata.create_all(bind=engine)


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