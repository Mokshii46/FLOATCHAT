"""
Seed the database with REAL Argo float data from the Argovis API.

Replaces the synthetic data from seed_db.py with actual Indian Ocean
observations. Runs the full pipeline:
    1. Wipe existing data
    2. Fetch metadata + profiles from Argovis REST API
    3. QC filter
    4. Load into SQLite/PostgreSQL
    5. Train ML trajectory models

Usage:
    python seed_real_data.py                  # default: 80 floats, 3 years
    python seed_real_data.py --max-floats 30  # fewer floats (faster)
    python seed_real_data.py --years 1        # shorter lookback
    python seed_real_data.py --skip-wipe      # don't wipe existing data (append)
    python seed_real_data.py --skip-training  # skip ML training step
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Ensure imports work when run from project root
sys.path.insert(0, str(Path(__file__).parent))

from database import engine, init_db
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger(__name__)


def wipe_database() -> None:
    """Delete all rows from data tables (preserves schema)."""
    tables = ["bgc_profiles", "profiles", "trajectory_points", "float_metadata"]
    with engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
                logger.info("  Cleared table: %s", table)
            except Exception as exc:
                logger.warning("  Could not clear %s: %s", table, exc)
        conn.commit()
    logger.info("Database wiped.")


def print_db_summary() -> None:
    """Print row counts for all tables."""
    tables = ["float_metadata", "profiles", "trajectory_points", "bgc_profiles"]
    print("\n" + "=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)
    with engine.connect() as conn:
        for table in tables:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table:25s}: {count:,} rows")
            except Exception:
                print(f"  {table:25s}: (table missing)")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Seed FloatChat DB with real Argovis data")
    parser.add_argument("--max-floats", type=int, default=80,
                        help="Max number of floats to fetch (default: 80)")
    parser.add_argument("--years", type=int, default=3,
                        help="Years of historical data (default: 3)")
    parser.add_argument("--skip-wipe", action="store_true",
                        help="Don't wipe existing data — append instead")
    parser.add_argument("--skip-training", action="store_true",
                        help="Skip ML trajectory training step")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")
    args = parser.parse_args()

    # ── Check API key ─────────────────────────────────────────────
    from config import settings
    if not settings.argovis_api_key:
        print("\n⚠️  No ARGOVIS_API_KEY found in .env!")
        print("   The API will work but with aggressive rate limiting.")
        print("   Get a free key at: https://argovis-keygen.colorado.edu/")
        print()

    # ── Confirmation ──────────────────────────────────────────────
    if not args.yes and not args.skip_wipe:
        print(f"\nThis will:")
        print(f"  1. WIPE all existing data in floatchat.db")
        print(f"  2. Fetch real data for up to {args.max_floats} Indian Ocean floats ({args.years} years)")
        print(f"  3. Load into database and train ML models")
        print()
        confirm = input("Continue? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    start_time = datetime.now()
    print(f"\n[+] FloatChat Real Data Seeder")
    print(f"   Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Config: max_floats={args.max_floats}, years={args.years}")
    print()

    # ── Step 1: Init DB ───────────────────────────────────────────
    print("[*] Step 1: Initializing database schema …")
    init_db()

    # ── Step 2: Wipe ──────────────────────────────────────────────
    if not args.skip_wipe:
        print("[*] Step 2: Wiping existing data …")
        wipe_database()
    else:
        print("[*] Step 2: Skipping wipe (append mode)")

    # ── Step 3: Fetch from Argovis ────────────────────────────────
    print(f"[*] Step 3: Fetching data from Argovis API …")
    print(f"   (This may take a few minutes depending on the number of floats)")
    print()

    from etl.fetch_argovis import fetch_indian_ocean_data
    data = fetch_indian_ocean_data(
        max_floats=args.max_floats,
        years_back=args.years,
    )

    float_metas = data["float_metadata"]
    profiles = data["profiles"]
    trajectories = data["trajectories"]
    bgc_profiles = data["bgc_profiles"]

    if not profiles:
        print("\n[!] No profile data fetched. Check your API key and internet connection.")
        print("   Get a free API key at: https://argovis-keygen.colorado.edu/")
        return

    print(f"\n   Fetched: {len(float_metas)} floats, {len(profiles):,} profiles, "
          f"{len(trajectories):,} trajectories, {len(bgc_profiles):,} BGC levels")

    # ── Step 4: QC filter ─────────────────────────────────────────
    print("\n[*] Step 4: Applying QC filters …")
    from etl.qc_filter import filter_profiles, filter_bgc_profiles

    profiles = filter_profiles(profiles)
    if bgc_profiles:
        bgc_profiles = filter_bgc_profiles(bgc_profiles)

    print(f"   After QC: {len(profiles):,} profiles, {len(bgc_profiles):,} BGC levels")

    # ── Step 5: Load into DB ──────────────────────────────────────
    print("\n[*] Step 5: Loading data into database …")

    # Insert float metadata first
    from etl.load_to_db import load_profiles, load_trajectory_points, load_bgc_profiles
    from database import session_scope
    from models.float_metadata import FloatMetadata

    with session_scope() as db:
        for meta in float_metas:
            existing = db.query(FloatMetadata).filter_by(wmo_id=meta["wmo_id"]).first()
            if existing:
                continue
            deploy_d = meta.get("deploy_date")
            if isinstance(deploy_d, str):
                try:
                    deploy_d = datetime.strptime(deploy_d, "%Y-%m-%d").date()
                except ValueError:
                    deploy_d = None
            elif isinstance(deploy_d, datetime):
                deploy_d = deploy_d.date()

            fm = FloatMetadata(
                wmo_id=meta["wmo_id"],
                dac=meta.get("dac", ""),
                platform_type=meta.get("platform_type", ""),
                project_name=meta.get("project_name", ""),
                pi_name=meta.get("pi_name", ""),
                deploy_date=deploy_d,
                deploy_lat=meta.get("deploy_lat"),
                deploy_lon=meta.get("deploy_lon"),
                is_bgc=meta.get("is_bgc", False),
                status=meta.get("status", "active"),
            )
            db.add(fm)
        db.flush()

    n_profiles = load_profiles(profiles)
    n_traj = load_trajectory_points(trajectories)
    n_bgc = load_bgc_profiles(bgc_profiles) if bgc_profiles else 0

    print(f"   Loaded: {n_profiles:,} profiles, {n_traj:,} trajectories, {n_bgc:,} BGC")

    # ── Step 6: Train ML models ───────────────────────────────────
    if not args.skip_training:
        print("\n[*] Step 6: Training trajectory prediction models …")
        try:
            from ml.train_trajectory import train_all
            trained, skipped = train_all()
            print(f"   Trained: {trained} models, Skipped: {skipped} (insufficient data)")
        except Exception as exc:
            logger.warning("ML training failed: %s", exc)
            print(f"   [!] Training failed: {exc}")
            print("   You can retry later with: python -m ml.train_trajectory")
    else:
        print("\n[*] Step 6: Skipping ML training")

    # ── Summary ───────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    print_db_summary()
    print(f"[OK] Done in {elapsed:.0f} seconds ({elapsed / 60:.1f} minutes)")
    print()


if __name__ == "__main__":
    main()
