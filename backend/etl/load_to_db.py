"""
Bulk-load cleaned DataFrames into Postgres. Upserts float_metadata (so
re-runs don't duplicate floats), then bulk-inserts profiles / bgc_profiles
/ trajectory_points.
"""

from __future__ import annotations

import logging

import pandas as pd
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database import session_scope
from models import FloatMetadata, Profile, TrajectoryPoint, BGCProfile

logger = logging.getLogger(__name__)


def upsert_float_metadata(meta_df: pd.DataFrame, is_bgc: bool = False) -> dict[str, int]:
    """Insert/update float_metadata rows; returns {wmo_id: db_id} mapping."""
    wmo_to_id: dict[str, int] = {}
    with session_scope() as db:
        for _, row in meta_df.iterrows():
            stmt = (
                pg_insert(FloatMetadata)
                .values(
                    wmo_id=row.get("wmo_id"),
                    dac=row.get("dac"),
                    platform_type=row.get("platform_type"),
                    project_name=row.get("project_name"),
                    pi_name=row.get("pi_name"),
                    is_bgc=is_bgc,
                )
                .on_conflict_do_update(
                    index_elements=["wmo_id"],
                    set_={"is_bgc": is_bgc},
                )
                .returning(FloatMetadata.id, FloatMetadata.wmo_id)
            )
            result = db.execute(stmt).fetchone()
            if result:
                wmo_to_id[result.wmo_id] = result.id

        # Fill in any that already existed and weren't returned above
        existing = db.query(FloatMetadata).filter(FloatMetadata.wmo_id.in_(meta_df["wmo_id"])).all()
        for f in existing:
            wmo_to_id[f.wmo_id] = f.id

    logger.info("Upserted %d floats", len(wmo_to_id))
    return wmo_to_id


def load_profiles(df: pd.DataFrame, wmo_to_id: dict[str, int], batch_size: int = 5000) -> int:
    df = df.copy()
    df["float_id"] = df["wmo_id"].map(wmo_to_id)
    df = df.dropna(subset=["float_id"])

    rows = []
    for _, r in df.iterrows():
        point = from_shape(Point(r["lon"], r["lat"]), srid=4326)
        rows.append(
            dict(
                float_id=int(r["float_id"]),
                cycle_number=int(r["cycle_number"]),
                timestamp=r["timestamp"],
                lat=r["lat"],
                lon=r["lon"],
                geom=point,
                pressure=r["pressure"],
                temperature=r.get("temperature"),
                salinity=r.get("salinity"),
                pressure_qc=r.get("pressure_qc"),
                temperature_qc=r.get("temperature_qc"),
                salinity_qc=r.get("salinity_qc"),
            )
        )

    with session_scope() as db:
        for i in range(0, len(rows), batch_size):
            db.bulk_insert_mappings(Profile, rows[i : i + batch_size])

    logger.info("Loaded %d profile rows", len(rows))
    return len(rows)


def load_bgc_profiles(df: pd.DataFrame, wmo_to_id: dict[str, int], batch_size: int = 5000) -> int:
    if df.empty:
        return 0
    df = df.copy()
    df["float_id"] = df["wmo_id"].map(wmo_to_id)
    df = df.dropna(subset=["float_id"])

    rows = []
    for _, r in df.iterrows():
        rows.append(
            dict(
                float_id=int(r["float_id"]),
                cycle_number=int(r["cycle_number"]),
                timestamp=r["timestamp"],
                lat=r["lat"],
                lon=r["lon"],
                pressure=r["pressure"],
                dissolved_oxygen=r.get("dissolved_oxygen"),
                chlorophyll=r.get("chlorophyll"),
                ph=r.get("ph"),
                nitrate=r.get("nitrate"),
                backscatter=r.get("backscatter"),
                dissolved_oxygen_qc=r.get("dissolved_oxygen_qc"),
                chlorophyll_qc=r.get("chlorophyll_qc"),
                ph_qc=r.get("ph_qc"),
                nitrate_qc=r.get("nitrate_qc"),
            )
        )

    with session_scope() as db:
        for i in range(0, len(rows), batch_size):
            db.bulk_insert_mappings(BGCProfile, rows[i : i + batch_size])

    logger.info("Loaded %d BGC profile rows", len(rows))
    return len(rows)


def load_trajectory_points(df: pd.DataFrame, wmo_to_id: dict[str, int]) -> int:
    """One row per (float, cycle) surfacing position, deduped from the profile rows."""
    traj_df = df.drop_duplicates(subset=["wmo_id", "cycle_number"])[
        ["wmo_id", "cycle_number", "timestamp", "lat", "lon"]
    ]

    rows = []
    for _, r in traj_df.iterrows():
        float_id = wmo_to_id.get(r["wmo_id"])
        if float_id is None:
            continue
        point = from_shape(Point(r["lon"], r["lat"]), srid=4326)
        rows.append(
            dict(
                float_id=float_id,
                cycle_number=int(r["cycle_number"]),
                timestamp=r["timestamp"],
                lat=r["lat"],
                lon=r["lon"],
                geom=point,
            )
        )

    with session_scope() as db:
        stmt = pg_insert(TrajectoryPoint).on_conflict_do_nothing(
            index_elements=["float_id", "cycle_number"]
        )
        if rows:
            db.execute(stmt, rows)

    logger.info("Loaded %d trajectory points", len(rows))
    return len(rows)