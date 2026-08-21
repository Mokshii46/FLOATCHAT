"""
APScheduler-based nightly refresh of ARGO data.

The scheduler runs the full ETL pipeline (fetch → parse → QC → load)
once per day at 02:00 UTC by default.  It is started from main.py on
FastAPI startup.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline() -> None:
    """Full ETL run: fetch → parse → qc → load."""
    logger.info("Scheduled ETL pipeline starting …")
    try:
        from etl.fetch_argo import fetch_by_region
        from etl.parse_netcdf import parse_profiles, parse_trajectory
        from etl.qc_filter import filter_profiles
        from etl.load_to_db import load_profiles, load_trajectory_points

        ds = fetch_by_region()
        profile_rows = parse_profiles(ds)
        traj_rows = parse_trajectory(ds)
        profile_rows = filter_profiles(profile_rows)

        load_profiles(profile_rows)
        load_trajectory_points(traj_rows)
        logger.info("Scheduled ETL pipeline completed.")
    except Exception as exc:
        logger.error("ETL pipeline failed: %s", exc, exc_info=True)


def start_scheduler(cron: str = "0 2 * * *") -> BackgroundScheduler:
    """
    Start and return a BackgroundScheduler that calls run_pipeline()
    on the given cron expression (default: 02:00 UTC daily).
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger.from_crontab(cron),
        id="argo_refresh",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler started with cron '%s'.", cron)
    return scheduler