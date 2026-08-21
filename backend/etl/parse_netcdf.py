"""
Flatten ARGO NetCDF (xarray Dataset, one row per obs point) into tabular
pandas DataFrames ready for loading into `profiles` / `bgc_profiles`.

Core physical variables (PRES, TEMP, PSAL) are handled by
`flatten_core_profile`. BGC variables (DOXY, CHLA, PH_IN_SITU_TOTAL,
NITRATE) are handled separately by `flatten_bgc_profile`, since they only
exist on *_Sprof.nc files for BGC-equipped floats (USP 7).
"""

from __future__ import annotations

import logging

import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)

CORE_VARS = {
    "PRES": "pressure",
    "TEMP": "temperature",
    "PSAL": "salinity",
    "PRES_QC": "pressure_qc",
    "TEMP_QC": "temperature_qc",
    "PSAL_QC": "salinity_qc",
}

BGC_VARS = {
    "PRES": "pressure",
    "DOXY": "dissolved_oxygen",
    "CHLA": "chlorophyll",
    "PH_IN_SITU_TOTAL": "ph",
    "NITRATE": "nitrate",
    "BBP700": "backscatter",
    "DOXY_QC": "dissolved_oxygen_qc",
    "CHLA_QC": "chlorophyll_qc",
    "PH_IN_SITU_TOTAL_QC": "ph_qc",
    "NITRATE_QC": "nitrate_qc",
}


def _base_frame(ds: xr.Dataset) -> pd.DataFrame:
    """Common identifying columns present on every ARGO profile dataset."""
    df = ds[["PLATFORM_NUMBER", "CYCLE_NUMBER", "TIME", "LATITUDE", "LONGITUDE"]].to_dataframe()
    df = df.reset_index(drop=True)
    df = df.rename(
        columns={
            "PLATFORM_NUMBER": "wmo_id",
            "CYCLE_NUMBER": "cycle_number",
            "TIME": "timestamp",
            "LATITUDE": "lat",
            "LONGITUDE": "lon",
        }
    )
    df["wmo_id"] = df["wmo_id"].astype(str).str.strip()
    return df


def flatten_core_profile(ds: xr.Dataset) -> pd.DataFrame:
    """xarray Dataset -> DataFrame with one row per (float, cycle, pressure level)."""
    base = _base_frame(ds)

    available = {k: v for k, v in CORE_VARS.items() if k in ds}
    var_df = ds[list(available.keys())].to_dataframe().reset_index(drop=True)
    var_df = var_df.rename(columns=available)

    df = pd.concat([base, var_df], axis=1)
    df = df.dropna(subset=["pressure"])
    logger.info("Flattened core profile: %d rows", len(df))
    return df


def flatten_bgc_profile(ds: xr.Dataset) -> pd.DataFrame:
    """Same as flatten_core_profile but for BGC variables (*_Sprof.nc)."""
    base = _base_frame(ds)

    available = {k: v for k, v in BGC_VARS.items() if k in ds}
    if not available:
        logger.warning("No BGC variables found in dataset — is this a core-only float?")
        return pd.DataFrame()

    var_df = ds[list(available.keys())].to_dataframe().reset_index(drop=True)
    var_df = var_df.rename(columns=available)

    df = pd.concat([base, var_df], axis=1)
    df = df.dropna(subset=["pressure"])
    logger.info("Flattened BGC profile: %d rows", len(df))
    return df


def extract_float_metadata(ds: xr.Dataset) -> pd.DataFrame:
    """One row per unique WMO id, for the float_metadata table."""
    cols = [c for c in ["PLATFORM_NUMBER", "DATA_CENTRE", "PLATFORM_TYPE", "PROJECT_NAME", "PI_NAME"] if c in ds]
    df = ds[cols].to_dataframe().reset_index(drop=True)
    df = df.rename(
        columns={
            "PLATFORM_NUMBER": "wmo_id",
            "DATA_CENTRE": "dac",
            "PLATFORM_TYPE": "platform_type",
            "PROJECT_NAME": "project_name",
            "PI_NAME": "pi_name",
        }
    )
    df["wmo_id"] = df["wmo_id"].astype(str).str.strip()
    df = df.drop_duplicates(subset=["wmo_id"])
    return df