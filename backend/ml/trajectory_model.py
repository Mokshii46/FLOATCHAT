"""
Trajectory model definition.

Two models are supported:
  1. LinearDrift  — weighted average of recent drift vectors (no ML, always available)
  2. GBMTrajectory — sklearn GradientBoostingRegressor trained per float

Both implement the same predict(lats, lons) → (next_lat, next_lon) interface.
"""

from __future__ import annotations

import numpy as np


class LinearDriftModel:
    """
    Weighted-average drift extrapolation.
    Weights: most recent cycle-to-cycle drift has highest weight.
    """

    def __init__(self, n_lags: int = 5):
        self.n_lags = n_lags

    def predict(self, lats: list[float], lons: list[float]) -> tuple[float, float]:
        n = len(lats)
        if n < 2:
            return lats[-1], lons[-1]

        dlats = [lats[i] - lats[i - 1] for i in range(1, n)]
        dlons = [lons[i] - lons[i - 1] for i in range(1, n)]

        use = dlats[-self.n_lags:], dlons[-self.n_lags:]
        weights = np.array([2 ** i for i in range(len(use[0]))], dtype=float)
        weights /= weights.sum()

        mean_dlat = float(np.dot(weights, use[0]))
        mean_dlon = float(np.dot(weights, use[1]))

        return lats[-1] + mean_dlat, lons[-1] + mean_dlon


class GBMTrajectoryModel:
    """
    GradientBoostingRegressor for per-float trajectory prediction.

    Features: last `window` latitudes and longitudes (2*window features).
    Two separate regressors: one for lat, one for lon.
    """

    def __init__(self, window: int = 5):
        self.window = window
        self.model_lat = None
        self.model_lon = None

    def _make_features(
        self,
        lats: list[float],
        lons: list[float],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build X (features), y_lat, y_lon arrays from position history."""
        w = self.window
        X, y_lat, y_lon = [], [], []
        for i in range(w, len(lats)):
            feat = lats[i - w:i] + lons[i - w:i]
            X.append(feat)
            y_lat.append(lats[i])
            y_lon.append(lons[i])
        return np.array(X), np.array(y_lat), np.array(y_lon)

    def fit(self, lats: list[float], lons: list[float]) -> None:
        from sklearn.ensemble import GradientBoostingRegressor

        X, y_lat, y_lon = self._make_features(lats, lons)
        if len(X) < 5:
            raise ValueError("Not enough samples to train GBM trajectory model.")

        self.model_lat = GradientBoostingRegressor(n_estimators=100, max_depth=3)
        self.model_lon = GradientBoostingRegressor(n_estimators=100, max_depth=3)
        self.model_lat.fit(X, y_lat)
        self.model_lon.fit(X, y_lon)

    def predict(self, lats: list[float], lons: list[float]) -> tuple[float, float]:
        if self.model_lat is None or self.model_lon is None:
            raise RuntimeError("GBMTrajectoryModel not trained.")
        w = self.window
        feat = np.array(lats[-w:] + lons[-w:]).reshape(1, -1)
        return float(self.model_lat.predict(feat)[0]), float(self.model_lon.predict(feat)[0])
