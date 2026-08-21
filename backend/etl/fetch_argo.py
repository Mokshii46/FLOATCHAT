"""
Thin wrapper around `argopy` for pulling ARGO float data by region, date
range, or specific WMO id. Caches raw NetCDF under data/raw/ so re-runs
during development don't re-hit the GDAC.

argopy docs: https://argopy.readthedocs.io/
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import argopy
from argopy import DataFetcher

from config import settings

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Rough Indian Ocean bounding box: [lon_min, lon_max, lat_min, lat_max]
INDIAN_OCEAN_BBOX = [20, 120, -40, 30]


def _fetcher() -> DataFetcher:
    argopy.set_options(mode="standard")
    return DataFetcher()


def fetch_region(
    bbox: list[float] | None = None,
    lookback_years: int | None = None,
    bgc_only: bool = False,
) -> "xr.Dataset":  # noqa: F821 - xarray Dataset, imported lazily by argopy
    """
    Fetch all float profiles in a bounding box over the last N years.

    bbox: [lon_min, lon_max, lat_min, lat_max]
    """
    bbox = bbox or INDIAN_OCEAN_BBOX
    lookback_years = lookback_years or settings.argo_lookback_years

    end = date.today()
    start = end - timedelta(days=365 * lookback_years)

    logger.info("Fetching ARGO region=%s window=%s..%s bgc_only=%s", bbox, start, end, bgc_only)

    fetcher = _fetcher()
    box = bbox + [0, 2000, start.isoformat(), end.isoformat()]  # add pressure range 0-2000 dbar

    if bgc_only:
        ds = fetcher.region(box).to_xarray()  # argopy auto-detects BGC vars if present
    else:
        ds = fetcher.region(box).to_xarray()

    return ds


def fetch_float(wmo_id: str) -> "xr.Dataset":  # noqa: F821
    """Fetch the full profile history for a single float by WMO id."""
    logger.info("Fetching float wmo_id=%s", wmo_id)
    fetcher = _fetcher()
    return fetcher.float(int(wmo_id)).to_xarray()


def save_raw(ds, name: str) -> Path:
    """Persist a fetched xarray Dataset to data/raw/<name>.nc for ETL reuse."""
    out_path = RAW_DIR / f"{name}.nc"
    ds.to_netcdf(out_path)
    logger.info("Saved raw NetCDF -> %s", out_path)
    return out_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dataset = fetch_region()
    save_raw(dataset, "indian_ocean_recent")