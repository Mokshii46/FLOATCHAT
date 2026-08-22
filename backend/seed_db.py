"""
Seed the SQLite database with realistic sample ARGO float data.

Run:  python seed_db.py
"""

from __future__ import annotations

import random
import math
from datetime import datetime, timedelta
from pathlib import Path

# Ensure we can import from the backend directory
import sys
sys.path.insert(0, str(Path(__file__).parent))

from database import engine, Base, init_db
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Realistic float metadata ─────────────────────────────────────

FLOATS_DATA = [
    # Indian Ocean floats (INCOIS)
    {"wmo_id": "2902183", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "M. Ravichandran", "deploy_lat": 15.2, "deploy_lon": 68.5, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902184", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "M. Ravichandran", "deploy_lat": 12.8, "deploy_lon": 72.3, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902190", "dac": "incois", "platform_type": "APEX", "project_name": "Indian Argo", "pi_name": "S. Prakash", "deploy_lat": 8.5, "deploy_lon": 88.7, "is_bgc": True, "status": "active"},
    {"wmo_id": "2902196", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "S. Prakash", "deploy_lat": 18.3, "deploy_lon": 65.1, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902201", "dac": "incois", "platform_type": "NOVA", "project_name": "Indian Argo", "pi_name": "A. Chatterjee", "deploy_lat": 10.5, "deploy_lon": 93.2, "is_bgc": True, "status": "active"},
    {"wmo_id": "2902215", "dac": "incois", "platform_type": "ARVOR", "project_name": "Bay of Bengal", "pi_name": "A. Chatterjee", "deploy_lat": 16.1, "deploy_lon": 85.6, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902220", "dac": "incois", "platform_type": "APEX", "project_name": "Bay of Bengal", "pi_name": "M. Ravichandran", "deploy_lat": 14.5, "deploy_lon": 82.3, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902225", "dac": "incois", "platform_type": "ARVOR", "project_name": "Arabian Sea", "pi_name": "S. Prakash", "deploy_lat": 20.1, "deploy_lon": 62.4, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902230", "dac": "incois", "platform_type": "PROVOR", "project_name": "Indian Argo BGC", "pi_name": "A. Chatterjee", "deploy_lat": 5.3, "deploy_lon": 78.9, "is_bgc": True, "status": "active"},
    {"wmo_id": "2902235", "dac": "incois", "platform_type": "ARVOR", "project_name": "Arabian Sea", "pi_name": "M. Ravichandran", "deploy_lat": 22.5, "deploy_lon": 58.7, "is_bgc": False, "status": "active"},
    # Coriolis floats
    {"wmo_id": "6903075", "dac": "coriolis", "platform_type": "ARVOR", "project_name": "CORIOLIS", "pi_name": "V. Thierry", "deploy_lat": -25.3, "deploy_lon": 55.8, "is_bgc": False, "status": "active"},
    {"wmo_id": "6903080", "dac": "coriolis", "platform_type": "PROVOR", "project_name": "CORIOLIS BGC", "pi_name": "H. Claustre", "deploy_lat": -30.5, "deploy_lon": 48.2, "is_bgc": True, "status": "active"},
    {"wmo_id": "6903085", "dac": "coriolis", "platform_type": "ARVOR", "project_name": "CORIOLIS", "pi_name": "V. Thierry", "deploy_lat": -15.7, "deploy_lon": 62.1, "is_bgc": False, "status": "active"},
    {"wmo_id": "6903090", "dac": "coriolis", "platform_type": "ARVOR", "project_name": "CORIOLIS", "pi_name": "V. Thierry", "deploy_lat": -20.4, "deploy_lon": 70.3, "is_bgc": False, "status": "active"},
    # CSIRO (Australia)
    {"wmo_id": "5905012", "dac": "csiro", "platform_type": "APEX", "project_name": "CSIRO Argo", "pi_name": "S. Wijffels", "deploy_lat": -35.2, "deploy_lon": 105.8, "is_bgc": False, "status": "active"},
    {"wmo_id": "5905018", "dac": "csiro", "platform_type": "APEX", "project_name": "CSIRO Argo", "pi_name": "S. Wijffels", "deploy_lat": -40.1, "deploy_lon": 95.3, "is_bgc": True, "status": "active"},
    # AOML (US)
    {"wmo_id": "4903456", "dac": "aoml", "platform_type": "APEX", "project_name": "US Argo", "pi_name": "R. Lumpkin", "deploy_lat": -10.5, "deploy_lon": 75.6, "is_bgc": False, "status": "active"},
    {"wmo_id": "4903462", "dac": "aoml", "platform_type": "SOLO", "project_name": "US Argo", "pi_name": "R. Lumpkin", "deploy_lat": -5.2, "deploy_lon": 85.3, "is_bgc": False, "status": "active"},
    # JMA (Japan)
    {"wmo_id": "2903783", "dac": "jma", "platform_type": "ARVOR", "project_name": "Japan Argo", "pi_name": "T. Suga", "deploy_lat": -8.5, "deploy_lon": 100.2, "is_bgc": False, "status": "active"},
    {"wmo_id": "2903790", "dac": "jma", "platform_type": "APEX", "project_name": "Japan Argo", "pi_name": "T. Suga", "deploy_lat": -12.3, "deploy_lon": 95.7, "is_bgc": False, "status": "active"},
    # Dead / inactive floats
    {"wmo_id": "2901850", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "M. Ravichandran", "deploy_lat": 11.2, "deploy_lon": 74.5, "is_bgc": False, "status": "dead"},
    {"wmo_id": "2901855", "dac": "incois", "platform_type": "APEX", "project_name": "Indian Argo", "pi_name": "S. Prakash", "deploy_lat": 9.8, "deploy_lon": 91.2, "is_bgc": False, "status": "dead"},
    # More active floats for density
    {"wmo_id": "2902240", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "M. Ravichandran", "deploy_lat": 7.2, "deploy_lon": 76.8, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902245", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "S. Prakash", "deploy_lat": 19.5, "deploy_lon": 70.2, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902250", "dac": "incois", "platform_type": "PROVOR", "project_name": "Indian Argo BGC", "pi_name": "A. Chatterjee", "deploy_lat": 13.4, "deploy_lon": 60.1, "is_bgc": True, "status": "active"},
    {"wmo_id": "6903095", "dac": "coriolis", "platform_type": "ARVOR", "project_name": "CORIOLIS", "pi_name": "V. Thierry", "deploy_lat": -45.2, "deploy_lon": 38.9, "is_bgc": False, "status": "active"},
    {"wmo_id": "6903100", "dac": "coriolis", "platform_type": "PROVOR", "project_name": "CORIOLIS BGC", "pi_name": "H. Claustre", "deploy_lat": -22.8, "deploy_lon": 42.5, "is_bgc": True, "status": "active"},
    {"wmo_id": "5905025", "dac": "csiro", "platform_type": "APEX", "project_name": "CSIRO Argo", "pi_name": "S. Wijffels", "deploy_lat": -28.6, "deploy_lon": 110.2, "is_bgc": False, "status": "active"},
    {"wmo_id": "4903470", "dac": "aoml", "platform_type": "SOLO", "project_name": "US Argo", "pi_name": "R. Lumpkin", "deploy_lat": 2.1, "deploy_lon": 68.4, "is_bgc": False, "status": "active"},
    {"wmo_id": "2903795", "dac": "jma", "platform_type": "ARVOR", "project_name": "Japan Argo", "pi_name": "T. Suga", "deploy_lat": -18.5, "deploy_lon": 108.3, "is_bgc": False, "status": "active"},
]


def _random_qc():
    """Return a realistic QC flag."""
    return random.choices(["1", "2", "3", "4"], weights=[80, 10, 5, 5])[0]


def _gen_profile_values(lat: float, depth_m: float, month: int):
    """Generate realistic T/S profiles based on location and depth."""
    # Temperature: warm at surface, decreases with depth
    # Tropical waters (~25-30°C surface), higher latitudes cooler
    base_sst = 28.0 - abs(lat) * 0.25
    # Seasonal variation
    seasonal = 1.5 * math.sin((month - 3) * math.pi / 6)
    surface_temp = base_sst + seasonal + random.gauss(0, 0.3)

    # Temperature decreases with depth (thermocline ~100-300m)
    if depth_m < 50:
        temp = surface_temp - depth_m * 0.01
    elif depth_m < 300:
        temp = surface_temp - 0.5 - (depth_m - 50) * 0.05
    elif depth_m < 1000:
        temp = surface_temp - 13.0 - (depth_m - 300) * 0.005
    else:
        temp = 2.0 + random.gauss(0, 0.2)

    temp = max(1.0, temp + random.gauss(0, 0.1))

    # Salinity: typically 34-36 PSU, varies by region
    base_sal = 35.0 + random.gauss(0, 0.1)
    if depth_m < 100:
        salinity = base_sal - 0.5 + random.gauss(0, 0.05)
    else:
        salinity = base_sal + 0.2 + random.gauss(0, 0.02)

    return round(temp, 3), round(salinity, 4)


def _gen_bgc_values(depth_m: float):
    """Generate realistic BGC values."""
    # Dissolved oxygen: higher at surface, minimum at ~500m
    if depth_m < 100:
        do = 220 + random.gauss(0, 10)
    elif depth_m < 500:
        do = 220 - (depth_m - 100) * 0.3 + random.gauss(0, 5)
    else:
        do = 100 + random.gauss(0, 10)

    # Chlorophyll: peak at ~50-100m (DCM)
    if depth_m < 20:
        chl = 0.15 + random.gauss(0, 0.05)
    elif depth_m < 100:
        chl = 0.5 + 0.8 * math.exp(-((depth_m - 70) ** 2) / 800) + random.gauss(0, 0.05)
    else:
        chl = 0.01 + random.gauss(0, 0.005)
    chl = max(0.001, chl)

    # pH: slightly lower at depth
    ph = 8.1 - depth_m * 0.0003 + random.gauss(0, 0.01)

    # Nitrate: low at surface, increases with depth
    if depth_m < 50:
        nitrate = 0.5 + random.gauss(0, 0.2)
    elif depth_m < 500:
        nitrate = 0.5 + (depth_m - 50) * 0.04 + random.gauss(0, 1)
    else:
        nitrate = 20 + random.gauss(0, 2)
    nitrate = max(0.01, nitrate)

    return round(do, 1), round(chl, 4), round(ph, 3), round(nitrate, 2)


def seed():
    """Populate the database with sample ARGO data."""
    init_db()

    with engine.connect() as conn:
        # Check if data already exists
        result = conn.execute(text("SELECT COUNT(*) FROM float_metadata"))
        count = result.scalar()
        if count and count > 5:
            logger.info("Database already has %d floats. Skipping seed.", count)
            return

        logger.info("Seeding database with %d floats...", len(FLOATS_DATA))

        # 1. Insert float_metadata
        for fd in FLOATS_DATA:
            deploy_date = (datetime.utcnow() - timedelta(days=random.randint(180, 1800))).strftime("%Y-%m-%d")
            conn.execute(text("""
                INSERT OR IGNORE INTO float_metadata
                (wmo_id, dac, platform_type, project_name, pi_name,
                 deploy_date, deploy_lat, deploy_lon, is_bgc, status)
                VALUES (:wmo_id, :dac, :platform_type, :project_name, :pi_name,
                        :deploy_date, :deploy_lat, :deploy_lon, :is_bgc, :status)
            """), {**fd, "deploy_date": deploy_date, "is_bgc": 1 if fd["is_bgc"] else 0})

        conn.commit()
        logger.info("Inserted %d floats.", len(FLOATS_DATA))

        # Get float IDs
        float_ids = {}
        for fd in FLOATS_DATA:
            result = conn.execute(
                text("SELECT id, deploy_lat, deploy_lon, is_bgc FROM float_metadata WHERE wmo_id = :wmo"),
                {"wmo": fd["wmo_id"]}
            )
            row = result.fetchone()
            if row:
                float_ids[fd["wmo_id"]] = {
                    "id": row[0], "lat": row[1], "lon": row[2], "is_bgc": row[3]
                }

        # 2. Insert trajectory_points (10-30 cycles per float)
        logger.info("Generating trajectory points...")
        for wmo_id, info in float_ids.items():
            float_id = info["id"]
            lat = info["lat"]
            lon = info["lon"]
            n_cycles = random.randint(10, 30)

            for cycle in range(1, n_cycles + 1):
                # Floats drift: ~0.1-0.5 degrees per cycle
                lat += random.gauss(0, 0.15)
                lon += random.gauss(0, 0.15)
                # Keep in reasonable bounds
                lat = max(-60, min(30, lat))
                lon = max(20, min(120, lon))

                ts = (datetime.utcnow() - timedelta(days=(n_cycles - cycle) * 10 + random.randint(0, 3))).strftime("%Y-%m-%d %H:%M:%S")

                # Predicted next position (simple linear extrapolation + noise)
                pred_lat = round(lat + random.gauss(0.05, 0.1), 4)
                pred_lon = round(lon + random.gauss(0.05, 0.1), 4)
                confidence = round(max(0.3, min(0.95, 0.75 + random.gauss(0, 0.15))), 2)

                conn.execute(text("""
                    INSERT INTO trajectory_points
                    (float_id, cycle_number, timestamp, lat, lon,
                     predicted_next_lat, predicted_next_lon, prediction_confidence)
                    VALUES (:fid, :cycle, :ts, :lat, :lon, :plat, :plon, :conf)
                """), {
                    "fid": float_id, "cycle": cycle, "ts": ts,
                    "lat": round(lat, 4), "lon": round(lon, 4),
                    "plat": pred_lat, "plon": pred_lon, "conf": confidence,
                })

        conn.commit()
        logger.info("Trajectory points inserted.")

        # 3. Insert profiles (multiple pressure levels per cycle)
        logger.info("Generating profile data...")
        pressure_levels = [5, 10, 20, 50, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000]

        for wmo_id, info in float_ids.items():
            float_id = info["id"]
            lat = info["lat"]
            lon = info["lon"]
            n_cycles = random.randint(8, 20)

            for cycle in range(1, n_cycles + 1):
                lat_c = lat + random.gauss(0, 0.1) * cycle * 0.1
                lon_c = lon + random.gauss(0, 0.1) * cycle * 0.1
                ts = (datetime.utcnow() - timedelta(days=(n_cycles - cycle) * 10 + random.randint(0, 3)))
                month = ts.month
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

                for pressure in pressure_levels:
                    temp, sal = _gen_profile_values(lat_c, pressure, month)
                    conn.execute(text("""
                        INSERT INTO profiles
                        (float_id, cycle_number, timestamp, lat, lon,
                         pressure, temperature, salinity,
                         pressure_qc, temperature_qc, salinity_qc)
                        VALUES (:fid, :cycle, :ts, :lat, :lon,
                                :pressure, :temp, :sal, :pqc, :tqc, :sqc)
                    """), {
                        "fid": float_id, "cycle": cycle, "ts": ts_str,
                        "lat": round(lat_c, 4), "lon": round(lon_c, 4),
                        "pressure": pressure, "temp": temp, "sal": sal,
                        "pqc": _random_qc(), "tqc": _random_qc(), "sqc": _random_qc(),
                    })

        conn.commit()
        logger.info("Profile data inserted.")

        # 4. Insert BGC profiles (only for BGC floats)
        logger.info("Generating BGC profile data...")
        bgc_floats = {k: v for k, v in float_ids.items() if v["is_bgc"]}
        bgc_pressures = [5, 10, 25, 50, 75, 100, 150, 200, 300, 500, 750, 1000]

        for wmo_id, info in bgc_floats.items():
            float_id = info["id"]
            lat = info["lat"]
            lon = info["lon"]
            n_cycles = random.randint(5, 15)

            for cycle in range(1, n_cycles + 1):
                lat_c = lat + random.gauss(0, 0.08) * cycle * 0.1
                lon_c = lon + random.gauss(0, 0.08) * cycle * 0.1
                ts = (datetime.utcnow() - timedelta(days=(n_cycles - cycle) * 10 + random.randint(0, 3)))
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

                for pressure in bgc_pressures:
                    do, chl, ph, nitrate = _gen_bgc_values(pressure)
                    conn.execute(text("""
                        INSERT INTO bgc_profiles
                        (float_id, cycle_number, timestamp, lat, lon, pressure,
                         dissolved_oxygen, chlorophyll, ph, nitrate,
                         dissolved_oxygen_qc, chlorophyll_qc, ph_qc, nitrate_qc)
                        VALUES (:fid, :cycle, :ts, :lat, :lon, :pressure,
                                :do, :chl, :ph, :nitrate, :doqc, :cqc, :pqc, :nqc)
                    """), {
                        "fid": float_id, "cycle": cycle, "ts": ts_str,
                        "lat": round(lat_c, 4), "lon": round(lon_c, 4),
                        "pressure": pressure,
                        "do": do, "chl": chl, "ph": ph, "nitrate": nitrate,
                        "doqc": _random_qc(), "cqc": _random_qc(),
                        "pqc": _random_qc(), "nqc": _random_qc(),
                    })

        conn.commit()
        logger.info("BGC profile data inserted.")

        # Summary
        for table in ["float_metadata", "profiles", "trajectory_points", "bgc_profiles"]:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            logger.info("  %s: %d rows", table, count)

    logger.info("Database seeding complete!")


if __name__ == "__main__":
    seed()
