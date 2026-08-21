#!/usr/bin/env python3
"""
Seed demo data for offline judging.

Loads a small, curated set of ARGO floats from the Indian Ocean into the DB
without requiring live internet access.  Data is synthetic but realistic.

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --floats 5 --cycles 20
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

# pyrefly: ignore [missing-import]
from database import init_db, session_scope
# pyrefly: ignore [missing-import]
from models.float_metadata import FloatMetadata
# pyrefly: ignore [missing-import]
from models.profile import Profile
# pyrefly: ignore [missing-import]
from models.trajectory import TrajectoryPoint
# pyrefly: ignore [missing-import]
from models.bgc_profile import BGCProfile


# ── Synthetic data parameters ──────────────────────────────────────

DEMO_FLOATS = [
    {"wmo_id": "2902183", "dac": "incois", "platform_type": "APEX",  "is_bgc": False,
     "deploy_lat": 12.5, "deploy_lon": 72.3, "region": "arabian_sea"},
    {"wmo_id": "2902200", "dac": "incois", "platform_type": "NOVA",  "is_bgc": False,
     "deploy_lat": 14.0, "deploy_lon": 68.5, "region": "arabian_sea"},
    {"wmo_id": "6904160", "dac": "coriolis", "platform_type": "NAVIS", "is_bgc": True,
     "deploy_lat": 10.2, "deploy_lon": 85.1, "region": "bay_of_bengal"},
    {"wmo_id": "6904161", "dac": "coriolis", "platform_type": "NAVIS", "is_bgc": True,
     "deploy_lat":  8.5, "deploy_lon": 83.0, "region": "bay_of_bengal"},
    {"wmo_id": "2903740", "dac": "incois", "platform_type": "APEX",  "is_bgc": False,
     "deploy_lat": -15.0, "deploy_lon": 65.0, "region": "south_indian_ocean"},
]


def _rand(base: float, noise: float) -> float:
    return round(base + random.uniform(-noise, noise), 4)


def generate_profiles(float_id: int, lat: float, lon: float, cycles: int) -> list:
    pressures = [5, 10, 25, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000]
    rows = []
    base_ts = datetime(2022, 1, 1)
    for c in range(1, cycles + 1):
        ts = base_ts + timedelta(days=(c - 1) * 10)
        clat = lat + random.uniform(-0.5, 0.5)
        clon = lon + random.uniform(-0.5, 0.5)
        for p in pressures:
            temp = max(-2.0, 28.0 - p * 0.012 + _rand(0, 0.5))
            sal  = 35.0 + _rand(0, 0.2) + p * 0.001
            rows.append(Profile(
                float_id=float_id,
                cycle_number=c,
                timestamp=ts,
                lat=round(clat, 4),
                lon=round(clon, 4),
                pressure=float(p),
                temperature=round(temp, 3),
                salinity=round(sal, 4),
                pressure_qc="1",
                temperature_qc="1",
                salinity_qc="1",
            ))
    return rows


def generate_trajectory(float_id: int, lat: float, lon: float, cycles: int) -> list:
    rows = []
    base_ts = datetime(2022, 1, 1)
    cur_lat, cur_lon = lat, lon
    for c in range(1, cycles + 1):
        ts = base_ts + timedelta(days=(c - 1) * 10)
        cur_lat += random.uniform(-0.3, 0.3)
        cur_lon += random.uniform(-0.2, 0.5)
        rows.append(TrajectoryPoint(
            float_id=float_id,
            cycle_number=c,
            timestamp=ts,
            lat=round(cur_lat, 4),
            lon=round(cur_lon, 4),
        ))
    return rows


def generate_bgc(float_id: int, lat: float, lon: float, cycles: int) -> list:
    pressures = [5, 10, 25, 50, 100, 200, 500, 1000]
    rows = []
    base_ts = datetime(2022, 1, 1)
    for c in range(1, cycles + 1):
        ts = base_ts + timedelta(days=(c - 1) * 10)
        for p in pressures:
            rows.append(BGCProfile(
                float_id=float_id,
                cycle_number=c,
                timestamp=ts,
                lat=round(lat + _rand(0, 0.3), 4),
                lon=round(lon + _rand(0, 0.3), 4),
                pressure=float(p),
                dissolved_oxygen=round(220.0 - p * 0.05 + _rand(0, 5), 2),
                chlorophyll=round(max(0, 0.5 - p * 0.0005 + _rand(0, 0.05)), 4),
                ph=round(8.1 - p * 0.00005 + _rand(0, 0.01), 4),
                nitrate=round(max(0, p * 0.02 + _rand(0, 0.5)), 3),
                backscatter=round(max(0, 0.001 - p * 0.0000005 + _rand(0, 0.0001)), 6),
                dissolved_oxygen_qc="1",
                chlorophyll_qc="1",
                ph_qc="1",
                nitrate_qc="1",
            ))
    return rows


def seed(n_floats: int = 5, n_cycles: int = 30) -> None:
    init_db()
    float_defs = DEMO_FLOATS[:n_floats]
    print(f"Seeding {len(float_defs)} floats × {n_cycles} cycles …")

    with session_scope() as db:
        for fd in float_defs:
            fm = db.query(FloatMetadata).filter_by(wmo_id=fd["wmo_id"]).first()
            if fm is None:
                fm = FloatMetadata(
                    wmo_id=fd["wmo_id"],
                    dac=fd["dac"],
                    platform_type=fd["platform_type"],
                    is_bgc=fd["is_bgc"],
                    deploy_lat=fd["deploy_lat"],
                    deploy_lon=fd["deploy_lon"],
                    deploy_date=datetime(2022, 1, 1).date(),
                    status="active",
                )
                db.add(fm)
                db.flush()

            db.add_all(generate_profiles(fm.id, fd["deploy_lat"], fd["deploy_lon"], n_cycles))
            db.add_all(generate_trajectory(fm.id, fd["deploy_lat"], fd["deploy_lon"], n_cycles))
            if fd["is_bgc"]:
                db.add_all(generate_bgc(fm.id, fd["deploy_lat"], fd["deploy_lon"], n_cycles))
            db.flush()
            print(f"  ✓ Float {fd['wmo_id']} ({fd['region']})")

    print("Seed complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--floats", type=int, default=5)
    parser.add_argument("--cycles", type=int, default=30)
    args = parser.parse_args()
    seed(args.floats, args.cycles)
