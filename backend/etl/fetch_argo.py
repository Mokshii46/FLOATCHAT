"""
ARGO data fetcher using argopy.

Downloads float data for the Indian Ocean by region bounding box or
specific WMO ids and caches raw NetCDF files under data/raw/.
"""

import os
from pathlib import Path
from typing import Optional

import argopy
from argopy import DataFetcher as ArgoDataFetcher

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Indian Ocean default bounding box: lon_min, lat_min, lon_max, lat_max
DEFAULT_BOX = [20.0, -60.0, 120.0, 30.0]


def fetch_by_region(
    box: Optional[list[float]] = None,
    years_back: Optional[int] = None,
    save_nc: bool = True,
) -> argopy.stores.ArgoIndex:
    """
    Fetch all floats in a geographic box for the last N years.

    Parameters
    ----------
    box        : [lon_min, lat_min, lon_max, lat_max]
    years_back : override settings.argo_lookback_years
    save_nc    : if True, save raw xarray dataset to data/raw/

    Returns
    -------
    ArgoIndex with combined dataset
    """
    box = box or DEFAULT_BOX
    years_back = years_back or settings.argo_lookback_years

    from datetime import datetime, timedelta

    date_end = datetime.utcnow().strftime("%Y-%m-%d")
    date_start = (datetime.utcnow() - timedelta(days=365 * years_back)).strftime("%Y-%m-%d")

    logger.info("Fetching ARGO data: box=%s, %s → %s", box, date_start, date_end)

    loader = ArgoDataFetcher(src="gdac", parallel=True).region(
        box + [date_start, date_end]
    )

    ds = loader.load().data
    logger.info("Fetched %d profiles.", ds.dims.get("N_POINTS", 0))

    if save_nc:
        out_path = RAW_DATA_DIR / f"region_{date_start}_{date_end}.nc"
        ds.to_netcdf(out_path)
        logger.info("Saved raw data to %s", out_path)

    return ds


def fetch_by_wmo(wmo_ids: list[str | int], save_nc: bool = True):
    """
    Fetch specific floats by WMO id list.

    Returns xarray Dataset.
    """
    ids = [int(w) for w in wmo_ids]
    logger.info("Fetching WMO ids: %s", ids)

    loader = ArgoDataFetcher(src="gdac").float(ids)
    ds = loader.load().data
    logger.info("Fetched %d points for %d floats.", ds.dims.get("N_POINTS", 0), len(ids))

    if save_nc:
        label = "_".join(str(i) for i in ids[:5])
        out_path = RAW_DATA_DIR / f"wmo_{label}.nc"
        ds.to_netcdf(out_path)
        logger.info("Saved raw data to %s", out_path)

    return ds


def list_cached_files() -> list[Path]:
    """Return all .nc files in the raw data cache."""
    return sorted(RAW_DATA_DIR.glob("*.nc"))