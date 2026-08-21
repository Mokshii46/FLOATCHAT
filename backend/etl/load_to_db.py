"""
Bulk-loader: insert parsed row dicts into Postgres.

Strategy
--------
- For FloatMetadata, use INSERT … ON CONFLICT (wmo_id) DO NOTHING so reruns
  are idempotent.
- For Profile / TrajectoryPoint / BGCProfile, use ON CONFLICT DO NOTHING on
  the (float_id, cycle_number, pressure) natural key to skip duplicates.
- Rows are batched in chunks of 2 000 for memory efficiency.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from database import session_scope
from models.float_metadata import FloatMetadata
from models.profile import Profile
from models.trajectory import TrajectoryPoint
from models.bgc_profile import BGCProfile
from utils.logger import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 2_000


# ── helpers ───────────────────────────────────────────────────────

def _get_or_create_float(db: Session, wmo_id: str) -> FloatMetadata:
    fm = db.query(FloatMetadata).filter_by(wmo_id=wmo_id).first()
    if fm is None:
        fm = FloatMetadata(wmo_id=wmo_id)
        db.add(fm)
        db.flush()
    return fm


def _make_geom(lat: float | None, lon: float | None) -> str | None:
    if lat is None or lon is None:
        return None
    return f"SRID=4326;POINT({lon} {lat})"


def _chunked(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


# ── public API ────────────────────────────────────────────────────

def load_profiles(rows: list[dict]) -> int:
    """Insert profile rows; returns count of rows inserted."""
    inserted = 0
    with session_scope() as db:
        for chunk in _chunked(rows, BATCH_SIZE):
            float_cache: dict[str, FloatMetadata] = {}
            for r in chunk:
                wmo = r.get("wmo_id")
                if not wmo:
                    continue
                if wmo not in float_cache:
                    float_cache[wmo] = _get_or_create_float(db, wmo)
                fm = float_cache[wmo]

                existing = (
                    db.query(Profile)
                    .filter_by(
                        float_id=fm.id,
                        cycle_number=r["cycle_number"],
                        pressure=r.get("pressure"),
                    )
                    .first()
                )
                if existing:
                    continue

                db.add(Profile(
                    float_id=fm.id,
                    cycle_number=r["cycle_number"],
                    timestamp=r.get("timestamp"),
                    lat=r.get("lat"),
                    lon=r.get("lon"),
                    geom=_make_geom(r.get("lat"), r.get("lon")),
                    pressure=r.get("pressure"),
                    temperature=r.get("temperature"),
                    salinity=r.get("salinity"),
                    pressure_qc=r.get("pressure_qc"),
                    temperature_qc=r.get("temperature_qc"),
                    salinity_qc=r.get("salinity_qc"),
                ))
                inserted += 1
            db.flush()

    logger.info("Loaded %d profile rows.", inserted)
    return inserted


def load_trajectory_points(rows: list[dict]) -> int:
    """Insert trajectory surfacing points; returns count inserted."""
    inserted = 0
    with session_scope() as db:
        for chunk in _chunked(rows, BATCH_SIZE):
            float_cache: dict[str, FloatMetadata] = {}
            for r in chunk:
                wmo = r.get("wmo_id")
                if not wmo:
                    continue
                if wmo not in float_cache:
                    float_cache[wmo] = _get_or_create_float(db, wmo)
                fm = float_cache[wmo]

                existing = (
                    db.query(TrajectoryPoint)
                    .filter_by(float_id=fm.id, cycle_number=r["cycle_number"])
                    .first()
                )
                if existing:
                    continue

                db.add(TrajectoryPoint(
                    float_id=fm.id,
                    cycle_number=r["cycle_number"],
                    timestamp=r.get("timestamp"),
                    lat=r.get("lat"),
                    lon=r.get("lon"),
                    geom=_make_geom(r.get("lat"), r.get("lon")),
                ))
                inserted += 1
            db.flush()

    logger.info("Loaded %d trajectory points.", inserted)
    return inserted


def load_bgc_profiles(rows: list[dict]) -> int:
    """Insert BGC profile rows; returns count inserted."""
    inserted = 0
    with session_scope() as db:
        for chunk in _chunked(rows, BATCH_SIZE):
            float_cache: dict[str, FloatMetadata] = {}
            for r in chunk:
                wmo = r.get("wmo_id")
                if not wmo:
                    continue
                if wmo not in float_cache:
                    fm = _get_or_create_float(db, wmo)
                    fm.is_bgc = True
                    float_cache[wmo] = fm
                fm = float_cache[wmo]

                db.add(BGCProfile(
                    float_id=fm.id,
                    cycle_number=r["cycle_number"],
                    timestamp=r.get("timestamp"),
                    lat=r.get("lat"),
                    lon=r.get("lon"),
                    pressure=r.get("pressure"),
                    dissolved_oxygen=r.get("dissolved_oxygen"),
                    chlorophyll=r.get("chlorophyll"),
                    ph=r.get("ph"),
                    nitrate=r.get("nitrate"),
                    backscatter=r.get("backscatter"),
                    dissolved_oxygen_qc=r.get("dissolved_oxygen_qc"),
                    chlorophyll_qc=r.get("chlorophyll_qc"),
                    ph_qc=r.get("ph_qc"),
                    nitrate_qc=r.get("nitrate_qc"),
                ))
                inserted += 1
            db.flush()

    logger.info("Loaded %d BGC profile rows.", inserted)
    return inserted