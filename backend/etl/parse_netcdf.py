"""
NetCDF parser — flattens xarray Datasets into tabular row dicts suitable
for bulk insertion into Postgres.

Physical profiles  → list of dicts matching models.Profile columns
Trajectory points  → list of dicts matching models.TrajectoryPoint columns
BGC profiles       → list of dicts matching models.BGCProfile columns (from *_Sprof.nc)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
# pyrefly: ignore [missing-import]
import xarray as xr

from utils.logger import get_logger

logger = get_logger(__name__)


def _safe_float(val: Any) -> float | None:
    """Convert numpy scalar or NaN to Python float or None."""
    try:
        v = float(val)
        return None if np.isnan(v) else v
    except (TypeError, ValueError):
        return None


def _safe_str(val: Any) -> str | None:
    try:
        s = str(val).strip()
        return s if s else None
    except Exception:
        return None


def parse_profiles(ds: xr.Dataset) -> list[dict]:
    """
    Flatten an argopy-loaded Dataset into Profile row dicts.

    Expected argopy standard variables:
      PLATFORM_NUMBER, CYCLE_NUMBER, JULD, LATITUDE, LONGITUDE,
      PRES, TEMP, PSAL, PRES_QC, TEMP_QC, PSAL_QC
    """
    rows = []
    n = ds.dims.get("N_POINTS", 0)
    logger.info("Parsing %d profile points …", n)

    wmo_arr = ds.get("PLATFORM_NUMBER", np.array([""] * n))
    cycle_arr = ds.get("CYCLE_NUMBER", np.zeros(n, dtype=int))
    juld_arr = ds.get("JULD", np.full(n, np.nan))
    lat_arr = ds.get("LATITUDE", np.full(n, np.nan))
    lon_arr = ds.get("LONGITUDE", np.full(n, np.nan))
    pres_arr = ds.get("PRES", np.full(n, np.nan))
    temp_arr = ds.get("TEMP", np.full(n, np.nan))
    psal_arr = ds.get("PSAL", np.full(n, np.nan))
    pres_qc_arr = ds.get("PRES_QC", np.full(n, ""))
    temp_qc_arr = ds.get("TEMP_QC", np.full(n, ""))
    psal_qc_arr = ds.get("PSAL_QC", np.full(n, ""))

    # argopy JULD is days since 1950-01-01
    epoch = datetime(1950, 1, 1)

    for i in range(n):
        try:
            juld_val = float(juld_arr[i]) if not np.isnan(float(juld_arr[i])) else None
            ts = epoch.__class__.fromordinal(epoch.toordinal() + int(juld_val)) if juld_val else None
        except Exception:
            ts = None

        rows.append({
            "wmo_id":        _safe_str(wmo_arr[i]),
            "cycle_number":  int(cycle_arr[i]),
            "timestamp":     ts,
            "lat":           _safe_float(lat_arr[i]),
            "lon":           _safe_float(lon_arr[i]),
            "pressure":      _safe_float(pres_arr[i]),
            "temperature":   _safe_float(temp_arr[i]),
            "salinity":      _safe_float(psal_arr[i]),
            "pressure_qc":   _safe_str(pres_qc_arr[i]),
            "temperature_qc":_safe_str(temp_qc_arr[i]),
            "salinity_qc":   _safe_str(psal_qc_arr[i]),
        })
    return rows


def parse_trajectory(ds: xr.Dataset) -> list[dict]:
    """
    Derive one trajectory point per (wmo_id, cycle_number) by taking
    the first lat/lon/timestamp within that cycle.
    """
    profile_rows = parse_profiles(ds)
    seen: dict[tuple, dict] = {}
    for r in profile_rows:
        key = (r["wmo_id"], r["cycle_number"])
        if key not in seen:
            seen[key] = {
                "wmo_id":       r["wmo_id"],
                "cycle_number": r["cycle_number"],
                "timestamp":    r["timestamp"],
                "lat":          r["lat"],
                "lon":          r["lon"],
            }
    return list(seen.values())


def parse_bgc_profiles(nc_path: Path) -> list[dict]:
    """
    Parse a *_Sprof.nc (BGC synthetic profile file) into BGCProfile row dicts.

    Variables attempted: DOXY, CHLA, PH_IN_SITU_TOTAL, NITRATE, BBP700,
    and their QC counterparts.
    """
    logger.info("Parsing BGC file: %s", nc_path)
    ds = xr.open_dataset(nc_path, decode_times=False)
    rows = []

    n_prof = ds.dims.get("N_PROF", 0)
    n_levels = ds.dims.get("N_LEVELS", 0)

    for i_prof in range(n_prof):
        wmo = _safe_str(ds.get("PLATFORM_NUMBER", [""] * n_prof)[i_prof])
        cycle = int(ds.get("CYCLE_NUMBER", [0] * n_prof)[i_prof])
        lat = _safe_float(ds.get("LATITUDE", [np.nan] * n_prof)[i_prof])
        lon = _safe_float(ds.get("LONGITUDE", [np.nan] * n_prof)[i_prof])
        juld = _safe_float(ds.get("JULD", [np.nan] * n_prof)[i_prof])

        ts: datetime | None
        try:
            epoch = datetime(1950, 1, 1)
            ts = epoch.__class__.fromordinal(epoch.toordinal() + int(juld)) if juld else None
        except Exception:
            ts = None

        for i_lvl in range(n_levels):
            def _get(var: str) -> float | None:
                arr = ds.get(var)
                if arr is None:
                    return None
                try:
                    return _safe_float(arr[i_prof, i_lvl])
                except Exception:
                    return None

            def _getq(var: str) -> str | None:
                arr = ds.get(var)
                if arr is None:
                    return None
                try:
                    return _safe_str(arr[i_prof, i_lvl])
                except Exception:
                    return None

            pres = _get("PRES")
            if pres is None:
                continue

            rows.append({
                "wmo_id":              wmo,
                "cycle_number":        cycle,
                "timestamp":           ts,
                "lat":                 lat,
                "lon":                 lon,
                "pressure":            pres,
                "dissolved_oxygen":    _get("DOXY"),
                "chlorophyll":         _get("CHLA"),
                "ph":                  _get("PH_IN_SITU_TOTAL"),
                "nitrate":             _get("NITRATE"),
                "backscatter":         _get("BBP700"),
                "dissolved_oxygen_qc": _getq("DOXY_QC"),
                "chlorophyll_qc":      _getq("CHLA_QC"),
                "ph_qc":               _getq("PH_IN_SITU_TOTAL_QC"),
                "nitrate_qc":          _getq("NITRATE_QC"),
            })
    return rows