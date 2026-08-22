"""
APScheduler-based nightly refresh of ARGO data.

The scheduler runs the full ETL pipeline via the Argovis REST API
once per day at 02:00 UTC by default.  It is started from main.py on
FastAPI startup.

If ARGOVIS_API_KEY is configured, uses the fast REST API path.
Otherwise, falls back to the legacy argopy/GDAC pipeline.
"""

# pyrefly: ignore [missing-import]
from apscheduler.schedulers.background import BackgroundScheduler
# pyrefly: ignore [missing-import]
from apscheduler.triggers.cron import CronTrigger

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def run_pipeline() -> None:
    """Full ETL run: fetch → QC → load (uses Argovis API or argopy fallback)."""
    logger.info("Scheduled ETL pipeline starting …")

    try:
        # Prefer Argovis REST API path
        from etl.fetch_argovis import fetch_indian_ocean_data
        from etl.qc_filter import filter_profiles, filter_bgc_profiles
        from etl.load_to_db import load_profiles, load_trajectory_points, load_bgc_profiles

        data = fetch_indian_ocean_data(max_floats=80)

        profiles = filter_profiles(data["profiles"])
        load_profiles(profiles)
        load_trajectory_points(data["trajectories"])

        if data["bgc_profiles"]:
            bgc = filter_bgc_profiles(data["bgc_profiles"])
            load_bgc_profiles(bgc)

        logger.info("Scheduled ETL pipeline completed (Argovis path).")
    except Exception as exc:
        logger.error("Argovis ETL pipeline failed: %s", exc, exc_info=True)
        logger.info("Falling back to legacy argopy pipeline …")
        _run_legacy_pipeline()


def _run_legacy_pipeline() -> None:
    """Fallback: fetch via argopy/GDAC (the original pipeline)."""
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
        logger.info("Scheduled ETL pipeline completed (legacy path).")
    except Exception as exc:
        logger.error("Legacy ETL pipeline also failed: %s", exc, exc_info=True)


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