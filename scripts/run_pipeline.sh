#!/usr/bin/env bash
# One-shot pipeline: fetch → parse → QC → load
# Usage: bash scripts/run_pipeline.sh [--wmo 2902183] [--years 3]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"

WMO_ID=""
YEARS=3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --wmo)   WMO_ID="$2"; shift 2 ;;
    --years) YEARS="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$BACKEND_DIR"

echo "=== FloatChat ETL Pipeline ==="
echo "  Backend dir : $BACKEND_DIR"
echo "  Lookback    : $YEARS years"
[ -n "$WMO_ID" ] && echo "  WMO id      : $WMO_ID"

python - <<PYEOF
import sys
sys.path.insert(0, ".")
from etl.fetch_argo import fetch_by_region, fetch_by_wmo
from etl.parse_netcdf import parse_profiles, parse_trajectory
from etl.qc_filter import filter_profiles
from etl.load_to_db import load_profiles, load_trajectory_points
from database import init_db

print("[1/5] Initialising database …")
init_db()

wmo_id = "${WMO_ID}"
years  = int("${YEARS}")

print("[2/5] Fetching ARGO data …")
if wmo_id:
    ds = fetch_by_wmo([wmo_id])
else:
    ds = fetch_by_region(years_back=years)

print("[3/5] Parsing NetCDF …")
profile_rows = parse_profiles(ds)
traj_rows    = parse_trajectory(ds)
print(f"      Parsed {len(profile_rows)} profile rows, {len(traj_rows)} trajectory points.")

print("[4/5] QC filtering …")
profile_rows = filter_profiles(profile_rows)

print("[5/5] Loading into database …")
n_prof = load_profiles(profile_rows)
n_traj = load_trajectory_points(traj_rows)
print(f"      Inserted {n_prof} profiles, {n_traj} trajectory points.")
print("=== Pipeline complete ===")
PYEOF
