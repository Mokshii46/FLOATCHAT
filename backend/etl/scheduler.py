"""
Periodic refresh job: re-fetches recent ARGO cycles and loads any new
data. Run standalone (`python -m etl.scheduler`) or import `start()`
from main.py to run inside the FastAPI process.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from etl.fetch_argo import fetch_region, save_raw
from etl.parse_netcdf import flatten_core_profile, flatten_bgc_profile, extract_float_metadata
from etl.qc_filter import qc_filter_core, qc_filter_bgc
from etl.load_to_db import upsert_float_metadata, load_profiles, load_bgc_profiles, load_trajectory_points

logger = logging.getLogger(__name__)


def refresh_job() -> None:
    logger.info("Scheduled ARGO refresh starting")
    try:
        ds = fetch_region(lookback_years=1)  # only need the recent tail for a refresh
        save_raw(ds, "refresh_latest")

        meta_df = extract_float_metadata(ds)
        wmo_to_id = upsert_float_metadata(meta_df)

        core_df = qc_filter_core(flatten_core_profile(ds))
        load_profiles(core_df, wmo_to_id)
        load_trajectory_points(core_df, wmo_to_id)

        bgc_df = qc_filter_bgc(flatten_bgc_profile(ds))
        if not bgc_df.empty:
            load_bgc_profiles(bgc_df, wmo_to_id)

        logger.info("Scheduled ARGO refresh complete")
    except Exception:
        logger.exception("Scheduled ARGO refresh failed")


def start(interval_hours: int = 24) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_job, "interval", hours=interval_hours, id="argo_refresh")
    scheduler.start()
    logger.info("ARGO refresh scheduler started (every %dh)", interval_hours)
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    refresh_job()