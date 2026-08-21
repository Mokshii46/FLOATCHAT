"""Tests for ETL parsing and QC filter."""

import pytest
from datetime import datetime

from etl.parse_netcdf import _safe_float, _safe_str
from etl.qc_filter import filter_profiles, filter_bgc_profiles, _qc_ok


# ── _safe_float ────────────────────────────────────────────────────

def test_safe_float_normal():
    assert _safe_float(12.5) == pytest.approx(12.5)

def test_safe_float_nan():
    import numpy as np
    assert _safe_float(np.nan) is None

def test_safe_float_none():
    assert _safe_float(None) is None


# ── QC filter ──────────────────────────────────────────────────────

def _make_row(pqc="1", tqc="1", sqc="1"):
    return {
        "wmo_id": "2902183",
        "cycle_number": 1,
        "timestamp": datetime.utcnow(),
        "lat": 10.0, "lon": 72.0,
        "pressure": 5.0,
        "temperature": 28.0,
        "salinity": 35.0,
        "pressure_qc": pqc,
        "temperature_qc": tqc,
        "salinity_qc": sqc,
    }


def test_qc_ok_good_flags():
    assert _qc_ok("1") is True
    assert _qc_ok("2") is True
    assert _qc_ok("5") is True
    assert _qc_ok("8") is True

def test_qc_ok_bad_flags():
    assert _qc_ok("4") is False
    assert _qc_ok("3") is False
    assert _qc_ok("9") is False

def test_filter_keeps_good():
    rows = [_make_row("1", "1", "1")]
    assert len(filter_profiles(rows)) == 1

def test_filter_drops_bad_pressure():
    rows = [_make_row("4", "1", "1")]
    assert len(filter_profiles(rows)) == 0

def test_filter_keeps_partial_bgc():
    """Row with only one good BGC param should still pass."""
    rows = [{
        "wmo_id": "6904160", "cycle_number": 1, "timestamp": datetime.utcnow(),
        "lat": 10.0, "lon": 85.0, "pressure": 50.0,
        "dissolved_oxygen": 200.0, "dissolved_oxygen_qc": "1",
        "chlorophyll": None, "chlorophyll_qc": "9",
        "ph": None, "ph_qc": None,
        "nitrate": None, "nitrate_qc": None,
    }]
    assert len(filter_bgc_profiles(rows)) == 1

def test_filter_drops_all_bad_bgc():
    rows = [{
        "wmo_id": "6904160", "cycle_number": 1, "timestamp": datetime.utcnow(),
        "lat": 10.0, "lon": 85.0, "pressure": 50.0,
        "dissolved_oxygen": None, "dissolved_oxygen_qc": "4",
        "chlorophyll": None, "chlorophyll_qc": "4",
        "ph": None, "ph_qc": "4",
        "nitrate": None, "nitrate_qc": "4",
    }]
    assert len(filter_bgc_profiles(rows)) == 0
