"""Tests for anomaly detection and anomaly service."""

import statistics
import pytest
from unittest.mock import patch

from ml.anomaly_detection import rolling_zscore, ZScoreResult


# ── rolling_zscore unit tests ──────────────────────────────────────

def test_rolling_zscore_normal_data():
    """Stable data with enough context should produce no anomalies."""
    # Use a longer series with larger window so early-window noise doesn't trigger
    values = [28.0, 28.1, 27.9, 28.0, 28.2, 27.8, 28.1, 28.0,
              27.9, 28.1, 28.0, 28.0, 28.1, 27.9, 28.0, 28.1,
              27.9, 28.0, 28.1, 28.0, 27.9, 28.0, 28.1, 28.0]
    result = rolling_zscore(values, window=12, threshold=2.5)
    assert isinstance(result, ZScoreResult)
    # With a wide enough threshold and sufficient history, stable data has no anomalies
    assert len(result.anomaly_indices) == 0, (
        f"Stable data should produce no anomalies at threshold=2.5, got {result.anomaly_indices}"
    )


def test_rolling_zscore_detects_spike():
    """A large spike after varied data should be detected."""
    # Need non-zero stdev in history for the spike to register
    values = [28.0, 28.1, 27.9, 28.0, 28.2, 27.8, 28.1, 28.0,
              27.9, 28.1, 28.0, 28.0, 35.0]  # 12 varied points, then a 7°C spike
    result = rolling_zscore(values, window=12, threshold=2.0)
    assert 12 in result.anomaly_indices, (
        f"Spike at index 12 should be flagged, got anomalies at {result.anomaly_indices}"
    )


def test_rolling_zscore_short_series():
    """Very short series should not crash or produce spurious results."""
    result = rolling_zscore([28.0], window=12, threshold=2.0)
    assert len(result.anomaly_indices) == 0
    assert result.z_scores == [0.0]


# ── anomaly_service: Bay of Bengal false-positive test ──────────────

def _make_bob_monthly_rows(n_months=24, base_temp=28.5, variation=0.3):
    """Generate synthetic Bay of Bengal monthly temperature rows.

    Returns rows sorted chronologically (ASC) as the fixed anomaly_service
    now expects, simulating normal seasonal variation.
    """
    import random
    random.seed(42)
    rows = []
    for i in range(n_months):
        month_str = f"2024-{(i % 12) + 1:02d}"
        val = base_temp + random.uniform(-variation, variation)
        rows.append({"month": month_str, "mean_val": round(val, 3)})
    return rows


def test_bob_normal_data_no_false_positive():
    """Bay of Bengal temperature with normal variation should NOT trigger anomaly."""
    from services.anomaly_service import detect_anomaly

    rows = _make_bob_monthly_rows(n_months=24, base_temp=28.5, variation=0.3)

    with patch("services.anomaly_service.execute_query", return_value=rows):
        result = detect_anomaly(region="bay_of_bengal", parameter="temperature")

    assert result.severity == "normal", (
        f"Normal BoB data should be 'normal', got '{result.severity}' (z={result.z_score})"
    )


def test_bob_genuine_anomaly_detected():
    """Bay of Bengal with a genuinely anomalous latest month SHOULD trigger."""
    from services.anomaly_service import detect_anomaly

    rows = _make_bob_monthly_rows(n_months=24, base_temp=28.5, variation=0.3)
    # Inject a 5°C spike into the last row
    rows[-1]["mean_val"] = 33.5

    with patch("services.anomaly_service.execute_query", return_value=rows):
        result = detect_anomaly(region="bay_of_bengal", parameter="temperature")

    assert result.severity in ("warning", "critical"), (
        f"5°C spike should trigger anomaly, got '{result.severity}' (z={result.z_score})"
    )
    assert abs(result.z_score) > 2.0


def test_bob_insufficient_data_returns_normal():
    """Fewer than MIN_POINTS rows should return 'normal' (insufficient data)."""
    from services.anomaly_service import detect_anomaly

    rows = [{"month": "2024-01", "mean_val": 28.0},
            {"month": "2024-02", "mean_val": 28.1}]

    with patch("services.anomaly_service.execute_query", return_value=rows):
        result = detect_anomaly(region="bay_of_bengal", parameter="temperature")

    assert result.severity == "normal"
    assert "Insufficient" in result.narrative
