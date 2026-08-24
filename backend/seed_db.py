"""
Seed the SQLite database with realistic sample ARGO float data evenly spread across all global water bodies.

Run:  python seed_db.py [--force]
"""

from __future__ import annotations

import random
import math
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure we can import from the backend directory
sys.path.insert(0, str(Path(__file__).parent))

from database import engine, Base, init_db
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Base realistic float metadata ─────────────────────────────────────

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
    # More active floats
    {"wmo_id": "2902240", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "M. Ravichandran", "deploy_lat": 7.2, "deploy_lon": 76.8, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902245", "dac": "incois", "platform_type": "ARVOR", "project_name": "Indian Argo", "pi_name": "S. Prakash", "deploy_lat": 19.5, "deploy_lon": 70.2, "is_bgc": False, "status": "active"},
    {"wmo_id": "2902250", "dac": "incois", "platform_type": "PROVOR", "project_name": "Indian Argo BGC", "pi_name": "A. Chatterjee", "deploy_lat": 13.4, "deploy_lon": 60.1, "is_bgc": True, "status": "active"},
    {"wmo_id": "6903095", "dac": "coriolis", "platform_type": "ARVOR", "project_name": "CORIOLIS", "pi_name": "V. Thierry", "deploy_lat": -45.2, "deploy_lon": 38.9, "is_bgc": False, "status": "active"},
    {"wmo_id": "6903100", "dac": "coriolis", "platform_type": "PROVOR", "project_name": "CORIOLIS BGC", "pi_name": "H. Claustre", "deploy_lat": -22.8, "deploy_lon": 42.5, "is_bgc": True, "status": "active"},
    {"wmo_id": "5905025", "dac": "csiro", "platform_type": "APEX", "project_name": "CSIRO Argo", "pi_name": "S. Wijffels", "deploy_lat": -28.6, "deploy_lon": 110.2, "is_bgc": False, "status": "active"},
    {"wmo_id": "4903470", "dac": "aoml", "platform_type": "SOLO", "project_name": "US Argo", "pi_name": "R. Lumpkin", "deploy_lat": 2.1, "deploy_lon": 68.4, "is_bgc": False, "status": "active"},
    {"wmo_id": "2903795", "dac": "jma", "platform_type": "ARVOR", "project_name": "Japan Argo", "pi_name": "T. Suga", "deploy_lat": -18.5, "deploy_lon": 108.3, "is_bgc": False, "status": "active"},
]


def get_global_floats_data() -> list[dict]:
    """
    Generate an evenly spread, non-cluttered global ARGO fleet covering all major ocean basins.
    Total ~350-400 floats across all world oceans.
    """
    floats = list(FLOATS_DATA)
    existing_wmos = {f["wmo_id"] for f in floats}

    # Clean water-bound oceanic basins (strictly avoiding landmasses)
    global_basins = [
        # --- INDIAN OCEAN BASIN ---
        ("Arabian Sea", 10.0, 23.0, 56.0, 73.0, 18, 0.35, ["incois", "aoml", "coriolis"], ["M. Ravichandran", "S. Prakash", "V. Thierry"]),
        ("Bay of Bengal", 8.0, 20.5, 82.0, 94.5, 18, 0.35, ["incois", "jma", "coriolis"], ["A. Chatterjee", "S. Prakash", "T. Suga"]),
        ("Equatorial & Central Indian Ocean", -18.0, 5.0, 52.0, 95.0, 25, 0.30, ["incois", "aoml", "csiro", "jma"], ["M. Ravichandran", "R. Lumpkin", "S. Wijffels"]),
        ("South Indian Ocean", -45.0, -20.0, 48.0, 108.0, 22, 0.25, ["csiro", "coriolis", "aoml"], ["S. Wijffels", "V. Thierry", "H. Claustre"]),
        ("Mozambique Channel & West Indian", -24.0, 8.0, 39.0, 52.0, 14, 0.25, ["coriolis", "incois", "aoml"], ["V. Thierry", "M. Ravichandran", "R. Lumpkin"]),

        # --- NORTH ATLANTIC OCEAN ---
        ("Tropical North Atlantic", 8.0, 22.0, -58.0, -25.0, 20, 0.30, ["aoml", "coriolis"], ["R. Lumpkin", "V. Thierry"]),
        ("Mid North Atlantic / Sargasso", 24.0, 44.0, -65.0, -28.0, 24, 0.30, ["aoml", "coriolis", "bodc"], ["R. Lumpkin", "V. Thierry", "M. Donnelly"]),
        ("Subpolar North Atlantic", 46.0, 60.0, -48.0, -15.0, 18, 0.25, ["bodc", "coriolis", "meds"], ["M. Donnelly", "H. Claustre", "J. Tremblay"]),

        # --- SOUTH ATLANTIC OCEAN ---
        ("Tropical South Atlantic", -18.0, -2.0, -32.0, 4.0, 18, 0.25, ["aoml", "coriolis"], ["R. Lumpkin", "V. Thierry"]),
        ("Central South Atlantic", -45.0, -20.0, -40.0, 10.0, 22, 0.25, ["coriolis", "aoml", "csiro"], ["H. Claustre", "R. Lumpkin", "S. Wijffels"]),

        # --- NORTH PACIFIC OCEAN ---
        ("Western North Pacific / Philippine Sea", 12.0, 32.0, 128.0, 155.0, 24, 0.30, ["jma", "kma", "aoml"], ["T. Suga", "K. Park", "R. Lumpkin"]),
        ("Northwest Pacific / Kuroshio Extension", 34.0, 48.0, 145.0, 175.0, 20, 0.30, ["jma", "aoml"], ["T. Suga", "R. Lumpkin"]),
        ("Central North Pacific (Hawaii Basin)", 15.0, 38.0, -175.0, -140.0, 24, 0.25, ["aoml", "jma"], ["R. Lumpkin", "T. Suga"]),
        ("Eastern North Pacific / California Current", 22.0, 48.0, -145.0, -122.0, 20, 0.30, ["aoml", "meds"], ["R. Lumpkin", "J. Tremblay"]),

        # --- SOUTH PACIFIC OCEAN ---
        ("Western South Pacific / Coral Sea", -35.0, -12.0, 152.0, 178.0, 22, 0.30, ["csiro", "jma"], ["S. Wijffels", "T. Suga"]),
        ("Central South Pacific Gyre", -38.0, -10.0, -170.0, -115.0, 24, 0.25, ["aoml", "csiro"], ["R. Lumpkin", "S. Wijffels"]),
        ("Eastern South Pacific / Peru-Chile", -42.0, -12.0, -105.0, -78.0, 18, 0.25, ["aoml", "coriolis"], ["R. Lumpkin", "H. Claustre"]),

        # --- SOUTHERN OCEAN (Circumpolar Ring) ---
        ("Southern Ocean (Atlantic Sector)", -62.0, -50.0, -45.0, 18.0, 16, 0.35, ["coriolis", "aoml"], ["H. Claustre", "R. Lumpkin"]),
        ("Southern Ocean (Indian Sector)", -62.0, -50.0, 35.0, 115.0, 18, 0.35, ["csiro", "coriolis", "incois"], ["S. Wijffels", "V. Thierry", "M. Ravichandran"]),
        ("Southern Ocean (Pacific Sector)", -62.0, -50.0, 135.0, -85.0, 20, 0.30, ["csiro", "aoml"], ["S. Wijffels", "R. Lumpkin"]),

        # --- ARCTIC & NORDIC SEAS ---
        ("Norwegian & Greenland Sea", 64.0, 76.0, -8.0, 18.0, 14, 0.25, ["coriolis", "bodc", "meds"], ["V. Thierry", "M. Donnelly", "J. Tremblay"]),
        ("Barents Sea & Arctic Basin", 71.0, 80.0, 24.0, 55.0, 12, 0.20, ["coriolis", "aoml"], ["V. Thierry", "R. Lumpkin"]),

        # --- MEDITERRANEAN SEA ---
        ("Mediterranean Sea", 33.5, 38.5, 3.0, 28.0, 12, 0.35, ["coriolis", "meds"], ["V. Thierry", "H. Claustre"]),
    ]

    random.seed(101)  # Fixed seed for perfectly reproducible, well-spaced float distribution
    wmo_counter = 2905000

    for reg_name, lat_min, lat_max, lon_min, lon_max, count, bgc_ratio, dacs, pis in global_basins:
        for _ in range(count):
            while str(wmo_counter) in existing_wmos:
                wmo_counter += 1
            wmo_id = str(wmo_counter)
            existing_wmos.add(wmo_id)
            wmo_counter += 1

            dac = random.choice(dacs)
            pi = random.choice(pis)

            # Handle cross-antimeridian longitude ranges if needed
            if lon_min > lon_max:
                lon = random.choice([
                    random.uniform(lon_min, 180.0),
                    random.uniform(-180.0, lon_max)
                ])
            else:
                lon = random.uniform(lon_min, lon_max)

            lat = random.uniform(lat_min, lat_max)
            is_bgc = random.random() < bgc_ratio
            ptype = random.choice(["ARVOR", "APEX", "PROVOR", "NOVA", "SOLO"])
            status = "active" if random.random() < 0.94 else "dead"

            floats.append({
                "wmo_id": wmo_id,
                "dac": dac,
                "platform_type": ptype,
                "project_name": f"{dac.upper()} {reg_name}",
                "pi_name": pi,
                "deploy_lat": round(lat, 2),
                "deploy_lon": round(lon, 2),
                "is_bgc": is_bgc,
                "status": status,
            })

    return floats


def _random_qc():
    """Return a realistic QC flag."""
    return random.choices(["1", "2", "3", "4"], weights=[82, 10, 5, 3])[0]


def _gen_profile_values(lat: float, depth_m: float, month: int):
    """Generate realistic T/S profiles based on latitude, depth, and seasonality."""
    abs_lat = abs(lat)
    if abs_lat < 25:
        base_sst = 28.0 - abs_lat * 0.25
    elif abs_lat < 55:
        base_sst = 22.0 - (abs_lat - 25) * 0.45
    else:
        base_sst = 6.0 - (abs_lat - 55) * 0.35
        base_sst = max(-1.8, base_sst)

    # Seasonal variation (opposite in southern hemisphere)
    hemisphere_sign = 1 if lat >= 0 else -1
    seasonal = 1.8 * math.sin((month - 3) * math.pi / 6) * hemisphere_sign
    surface_temp = max(-1.8, base_sst + seasonal + random.gauss(0, 0.25))

    # Temperature profile by depth
    if depth_m < 50:
        temp = surface_temp - depth_m * 0.01
    elif depth_m < 300:
        temp = surface_temp - 0.5 - (depth_m - 50) * 0.045
    elif depth_m < 1000:
        temp = surface_temp - 12.0 - (depth_m - 300) * 0.004
    else:
        temp = 1.8 + random.gauss(0, 0.15)

    temp = max(-1.8, temp + random.gauss(0, 0.08))

    # Salinity profile (typically 33.5 - 37.0 PSU)
    if abs_lat < 20:
        base_sal = 35.2 + random.gauss(0, 0.1)
    elif abs_lat < 40:
        base_sal = 36.2 + random.gauss(0, 0.1)  # Subtropical high evaporation
    else:
        base_sal = 34.0 + random.gauss(0, 0.1)  # High-latitude freshening

    if depth_m < 100:
        salinity = base_sal - 0.3 + random.gauss(0, 0.04)
    else:
        salinity = base_sal + 0.1 + random.gauss(0, 0.02)

    return round(temp, 3), round(salinity, 4)


def _gen_bgc_values(depth_m: float):
    """Generate realistic BGC values (DO, Chlorophyll, pH, Nitrate)."""
    if depth_m < 100:
        do = 230 + random.gauss(0, 8)
    elif depth_m < 500:
        do = 230 - (depth_m - 100) * 0.32 + random.gauss(0, 4)
    else:
        do = 110 + random.gauss(0, 8)

    if depth_m < 20:
        chl = 0.18 + random.gauss(0, 0.04)
    elif depth_m < 100:
        chl = 0.55 + 0.75 * math.exp(-((depth_m - 65) ** 2) / 750) + random.gauss(0, 0.04)
    else:
        chl = 0.01 + random.gauss(0, 0.004)
    chl = max(0.001, chl)

    ph = 8.12 - depth_m * 0.0003 + random.gauss(0, 0.01)

    if depth_m < 50:
        nitrate = 0.6 + random.gauss(0, 0.15)
    elif depth_m < 500:
        nitrate = 0.6 + (depth_m - 50) * 0.042 + random.gauss(0, 0.8)
    else:
        nitrate = 22 + random.gauss(0, 1.8)
    nitrate = max(0.01, nitrate)

    return round(do, 1), round(chl, 4), round(ph, 3), round(nitrate, 2)


def seed(force: bool = False):
    """Populate the database with global ARGO data across all ocean basins."""
    init_db()

    floats_to_insert = get_global_floats_data()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM float_metadata"))
        count = result.scalar()

        if count and count >= len(floats_to_insert) and not force:
            logger.info("Database already populated with %d floats. Skipping seed.", count)
            return

        if force or (count and count > 0):
            logger.info("Re-populating database with evenly distributed global float dataset...")
            for tbl in ["bgc_profiles", "profiles", "trajectory_points", "float_metadata"]:
                try:
                    conn.execute(text(f"DELETE FROM {tbl}"))
                except Exception:
                    pass
            conn.commit()

        logger.info("Seeding database with %d floats globally...", len(floats_to_insert))

        # 1. Insert float_metadata
        now_utc = datetime.now(timezone.utc)
        for fd in floats_to_insert:
            deploy_date = (now_utc - timedelta(days=random.randint(180, 1800))).strftime("%Y-%m-%d")
            conn.execute(text("""
                INSERT OR IGNORE INTO float_metadata
                (wmo_id, dac, platform_type, project_name, pi_name,
                 deploy_date, deploy_lat, deploy_lon, is_bgc, status)
                VALUES (:wmo_id, :dac, :platform_type, :project_name, :pi_name,
                        :deploy_date, :deploy_lat, :deploy_lon, :is_bgc, :status)
            """), {**fd, "deploy_date": deploy_date, "is_bgc": 1 if fd["is_bgc"] else 0})

        conn.commit()
        logger.info("Inserted %d floats into float_metadata.", len(floats_to_insert))

        # Get float IDs
        float_ids = {}
        for fd in floats_to_insert:
            result = conn.execute(
                text("SELECT id, deploy_lat, deploy_lon, is_bgc FROM float_metadata WHERE wmo_id = :wmo"),
                {"wmo": fd["wmo_id"]}
            )
            row = result.fetchone()
            if row:
                float_ids[fd["wmo_id"]] = {
                    "id": row[0], "lat": row[1], "lon": row[2], "is_bgc": row[3]
                }

        # 2. Insert trajectory_points (8-16 cycles per float)
        logger.info("Generating trajectory points...")
        for wmo_id, info in float_ids.items():
            float_id = info["id"]
            lat = info["lat"]
            lon = info["lon"]
            n_cycles = random.randint(8, 16)

            for cycle in range(1, n_cycles + 1):
                lat += random.gauss(0, 0.12)
                lon += random.gauss(0, 0.12)
                lat = max(-85, min(85, lat))
                if lon > 180:
                    lon -= 360
                elif lon < -180:
                    lon += 360

                ts = (now_utc - timedelta(days=(n_cycles - cycle) * 10 + random.randint(0, 3))).strftime("%Y-%m-%d %H:%M:%S")

                pred_lat = round(lat + random.gauss(0.04, 0.08), 4)
                pred_lon = round(lon + random.gauss(0.04, 0.08), 4)
                confidence = round(max(0.35, min(0.95, 0.78 + random.gauss(0, 0.12))), 2)

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
            n_cycles = random.randint(5, 12)

            for cycle in range(1, n_cycles + 1):
                lat_c = lat + random.gauss(0, 0.08) * cycle * 0.08
                lon_c = lon + random.gauss(0, 0.08) * cycle * 0.08
                ts = (now_utc - timedelta(days=(n_cycles - cycle) * 10 + random.randint(0, 3)))
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

        # 4. Insert BGC profiles (for BGC floats)
        logger.info("Generating BGC profile data...")
        bgc_floats = {k: v for k, v in float_ids.items() if v["is_bgc"]}
        bgc_pressures = [5, 10, 25, 50, 75, 100, 150, 200, 300, 500, 750, 1000]

        for wmo_id, info in bgc_floats.items():
            float_id = info["id"]
            lat = info["lat"]
            lon = info["lon"]
            n_cycles = random.randint(4, 10)

            for cycle in range(1, n_cycles + 1):
                lat_c = lat + random.gauss(0, 0.06) * cycle * 0.08
                lon_c = lon + random.gauss(0, 0.06) * cycle * 0.08
                ts = (now_utc - timedelta(days=(n_cycles - cycle) * 10 + random.randint(0, 3)))
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

    logger.info("Global database seeding complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed FloatChat database")
    parser.add_argument("--force", action="store_true", help="Force re-seed and overwrite existing floats")
    args = parser.parse_args()
    seed(force=args.force)
