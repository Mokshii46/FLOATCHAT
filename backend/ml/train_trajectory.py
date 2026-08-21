"""
Training script for per-float GBM trajectory models.

Usage:
    python -m ml.train_trajectory              # train all active floats
    python -m ml.train_trajectory --wmo 2902183  # train one float

Saves trained models to data/ml_models/traj_{wmo_id}.pkl
Minimum 15 trajectory points required to train; floats with fewer cycles
are silently skipped.
"""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

from database import SessionLocal
from models.float_metadata import FloatMetadata
from models.trajectory import TrajectoryPoint
from ml.trajectory_model import GBMTrajectoryModel
from utils.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parents[2] / "data" / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MIN_SAMPLES = 15


def train_float(wmo_id: str) -> bool:
    """
    Train GBM models for one float.
    Returns True on success, False on insufficient data.
    """
    db = SessionLocal()
    try:
        fm = db.query(FloatMetadata).filter_by(wmo_id=str(wmo_id)).first()
        if fm is None:
            logger.warning("Float %s not found in DB.", wmo_id)
            return False

        points = (
            db.query(TrajectoryPoint)
            .filter_by(float_id=fm.id)
            .order_by(TrajectoryPoint.cycle_number)
            .all()
        )

        lats = [p.lat for p in points if p.lat is not None]
        lons = [p.lon for p in points if p.lon is not None]

        if len(lats) < MIN_SAMPLES:
            logger.info("Skipping float %s — only %d trajectory points.", wmo_id, len(lats))
            return False

        model = GBMTrajectoryModel(window=5)
        model.fit(lats, lons)

        out_path = MODEL_DIR / f"traj_{wmo_id}.pkl"
        with open(out_path, "wb") as f:
            pickle.dump((model.model_lat, model.model_lon), f)

        logger.info("Trained and saved trajectory model for float %s.", wmo_id)
        return True
    except Exception as exc:
        logger.error("Training failed for float %s: %s", wmo_id, exc)
        return False
    finally:
        db.close()


def train_all() -> tuple[int, int]:
    """Train models for all active floats. Returns (trained, skipped)."""
    db = SessionLocal()
    try:
        wmo_ids = [f.wmo_id for f in db.query(FloatMetadata).filter_by(status="active").all()]
    finally:
        db.close()

    trained = 0
    skipped = 0
    for wmo in wmo_ids:
        if train_float(wmo):
            trained += 1
        else:
            skipped += 1

    logger.info("Training complete: %d trained, %d skipped.", trained, skipped)
    return trained, skipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train trajectory models")
    parser.add_argument("--wmo", type=str, default=None, help="Train a single float by WMO id")
    args = parser.parse_args()

    if args.wmo:
        ok = train_float(args.wmo)
        print("Trained." if ok else "Insufficient data or error.")
    else:
        t, s = train_all()
        print(f"Done. Trained: {t}, Skipped: {s}")
