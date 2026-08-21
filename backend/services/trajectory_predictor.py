"""
Trajectory predictor — USP 3.

Predicts the next surfacing lat/lon for a float using:
  1. Linear drift extrapolation (fast, no ML needed)
  2. Optional sklearn GradientBoostingRegressor if enough history exists

The predicted position is written back to trajectory_points so it's
available via the /floats/{wmo_id} endpoint and the frontend map layer.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from database import session_scope
from models.trajectory import TrajectoryPoint
from models.float_metadata import FloatMetadata
from utils.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parents[2] / "data" / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MIN_CYCLES_FOR_ML = 10   # fallback to linear extrapolation below this


@dataclass
class Prediction:
    wmo_id: str
    next_lat: float
    next_lon: float
    confidence: float
    method: str             # "linear" | "ml"


# ── Linear extrapolation ──────────────────────────────────────────

def _linear_extrapolate(lats: list[float], lons: list[float]) -> tuple[float, float]:
    """
    Simple weighted-average of the last 3 cycle-to-cycle drift vectors.
    Returns predicted (next_lat, next_lon).
    """
    n = len(lats)
    if n < 2:
        return lats[-1], lons[-1]

    dlats = [lats[i] - lats[i - 1] for i in range(1, n)]
    dlons = [lons[i] - lons[i - 1] for i in range(1, n)]

    # Weight: most recent drift counts more
    weights = [2 ** i for i in range(len(dlats))]
    w_sum = sum(weights)
    mean_dlat = sum(w * d for w, d in zip(weights, dlats)) / w_sum
    mean_dlon = sum(w * d for w, d in zip(weights, dlons)) / w_sum

    return lats[-1] + mean_dlat, lons[-1] + mean_dlon


# ── ML prediction ─────────────────────────────────────────────────

def _ml_predict(lats: list[float], lons: list[float], wmo_id: str) -> tuple[float, float] | None:
    """
    Load a trained GBM model for this float (if it exists) and predict.
    Returns (next_lat, next_lon) or None if no model found.
    """
    model_path = MODEL_DIR / f"traj_{wmo_id}.pkl"
    if not model_path.exists():
        return None
    try:
        with open(model_path, "rb") as f:
            model_lat, model_lon = pickle.load(f)
        # Feature: last 5 positions flattened
        window = 5
        if len(lats) < window:
            return None
        X = np.array(lats[-window:] + lons[-window:]).reshape(1, -1)
        pred_lat = float(model_lat.predict(X)[0])
        pred_lon = float(model_lon.predict(X)[0])
        return pred_lat, pred_lon
    except Exception as exc:
        logger.warning("ML prediction failed for %s: %s", wmo_id, exc)
        return None


# ── Public API ────────────────────────────────────────────────────

def predict_next_position(wmo_id: str) -> Prediction | None:
    """
    Predict next surfacing position for a float.
    Reads trajectory history from the DB, writes prediction back.
    """
    with session_scope() as db:
        fm = db.query(FloatMetadata).filter_by(wmo_id=str(wmo_id)).first()
        if fm is None:
            logger.warning("Float %s not found.", wmo_id)
            return None

        points = (
            db.query(TrajectoryPoint)
            .filter_by(float_id=fm.id)
            .order_by(TrajectoryPoint.cycle_number)
            .all()
        )

        if len(points) < 2:
            return None

        lats = [p.lat for p in points if p.lat is not None]
        lons = [p.lon for p in points if p.lon is not None]

        if len(lats) < 2:
            return None

        # Try ML first; fall back to linear
        ml_result = None
        if len(lats) >= MIN_CYCLES_FOR_ML:
            ml_result = _ml_predict(lats, lons, wmo_id)

        if ml_result:
            pred_lat, pred_lon = ml_result
            method = "ml"
            confidence = 0.70
        else:
            pred_lat, pred_lon = _linear_extrapolate(lats, lons)
            method = "linear"
            # Confidence decays with time since last observation
            confidence = max(0.30, 0.85 - 0.02 * len(lats))

        # Clamp to valid lat/lon
        pred_lat = max(-90.0, min(90.0, pred_lat))
        pred_lon = max(-180.0, min(180.0, pred_lon))

        # Write back to latest trajectory point
        latest = points[-1]
        latest.predicted_next_lat = pred_lat
        latest.predicted_next_lon = pred_lon
        latest.prediction_confidence = round(confidence, 3)
        db.flush()

    return Prediction(
        wmo_id=wmo_id,
        next_lat=round(pred_lat, 4),
        next_lon=round(pred_lon, 4),
        confidence=round(confidence, 3),
        method=method,
    )
