"""
Rolling z-score and change-point anomaly detection.

Used by services/anomaly_service.py and can also be run standalone
to pre-compute anomaly flags for all regions.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class ZScoreResult:
    values: list[float]
    z_scores: list[float]
    anomaly_indices: list[int]   # indices where |z| > threshold


def rolling_zscore(
    values: list[float],
    window: int = 12,
    threshold: float = 2.0,
) -> ZScoreResult:
    """
    Compute rolling z-scores for a time series.

    Parameters
    ----------
    values    : ordered time series values
    window    : rolling window size (default 12 months)
    threshold : flag observations where |z| > threshold

    Returns
    -------
    ZScoreResult with z_scores list and anomaly indices.
    """
    z_scores = []
    for i, v in enumerate(values):
        start = max(0, i - window)
        context = values[start:i] if i > 0 else [v]
        if len(context) < 2:
            z_scores.append(0.0)
            continue
        mu = statistics.mean(context)
        sigma = statistics.stdev(context)
        z = (v - mu) / sigma if sigma > 0 else 0.0
        z_scores.append(round(z, 3))

    anomalies = [i for i, z in enumerate(z_scores) if abs(z) > threshold]
    return ZScoreResult(values=values, z_scores=z_scores, anomaly_indices=anomalies)


@dataclass
class ChangePoint:
    index: int
    before_mean: float
    after_mean: float
    magnitude: float


def simple_changepoint(
    values: list[float],
    min_segment: int = 6,
) -> list[ChangePoint]:
    """
    Detect the single most significant change point in a time series
    using a sliding-window mean comparison.

    Returns a list of detected ChangePoint objects (typically 0 or 1 for
    short series).
    """
    n = len(values)
    if n < min_segment * 2:
        return []

    best_score = 0.0
    best_i = -1

    for i in range(min_segment, n - min_segment):
        before = values[:i]
        after = values[i:]
        m1 = statistics.mean(before)
        m2 = statistics.mean(after)
        score = abs(m2 - m1)
        if score > best_score:
            best_score = score
            best_i = i

    if best_i == -1:
        return []

    return [
        ChangePoint(
            index=best_i,
            before_mean=statistics.mean(values[:best_i]),
            after_mean=statistics.mean(values[best_i:]),
            magnitude=round(best_score, 4),
        )
    ]
