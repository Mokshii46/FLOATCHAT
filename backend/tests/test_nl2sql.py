"""Tests for NL2SQL routing and template matching."""

import pytest
from unittest.mock import patch, MagicMock

from nl2sql.router import (
    _tokenise,
    _extract_wmo,
    _extract_cycle,
    _detect_region,
    _fill_params,
)
from nl2sql.template_queries import TEMPLATES


# ── Tokeniser ──────────────────────────────────────────────────────

def test_tokenise_basic():
    tokens = _tokenise("What is the average temperature?")
    assert "temperature" in tokens
    assert "average" in tokens


def test_tokenise_removes_punctuation():
    tokens = _tokenise("hello, world!")
    assert "hello" in tokens
    assert "world" in tokens


# ── WMO extraction ─────────────────────────────────────────────────

def test_extract_wmo_found():
    assert _extract_wmo("Show me float 2902183 trajectory") == "2902183"

def test_extract_wmo_not_found():
    assert _extract_wmo("Show me temperature in Arabian Sea") is None


# ── Cycle extraction ───────────────────────────────────────────────

def test_extract_cycle_found():
    assert _extract_cycle("profile for cycle 45") == 45

def test_extract_cycle_hash():
    assert _extract_cycle("float 2902183 #12") == 12

def test_extract_cycle_not_found():
    assert _extract_cycle("no cycle number here") is None


# ── Region detection ───────────────────────────────────────────────

def test_detect_arabian_sea():
    bbox = _detect_region("temperature in the arabian sea")
    assert bbox is not None
    lat_min, lat_max, lon_min, lon_max = bbox
    assert lat_min < lat_max and lon_min < lon_max

def test_detect_bay_of_bengal():
    bbox = _detect_region("floats in bay of bengal")
    assert bbox is not None

def test_detect_none():
    assert _detect_region("random text with no region") is None


# ── Template coverage ──────────────────────────────────────────────

def test_all_templates_have_required_keys():
    for tmpl in TEMPLATES:
        assert "id" in tmpl
        assert "keywords" in tmpl
        assert "sql" in tmpl
        assert "params" in tmpl
        assert "description" in tmpl

def test_no_duplicate_template_ids():
    ids = [t["id"] for t in TEMPLATES]
    assert len(ids) == len(set(ids))


# ── Router integration (mocked DB/LLM) ────────────────────────────

def test_router_matches_float_trajectory():
    """The 'float trajectory' template should match WMO-containing questions."""
    from nl2sql.router import route

    with patch("nl2sql.router.validate", side_effect=lambda sql: sql):
        result = route("Show me the trajectory of float 2902183")

    assert result["source"] == "template"
    assert result["template"]["id"] == "float_trajectory"

def test_router_matches_list_floats():
    from nl2sql.router import route

    with patch("nl2sql.router.validate", side_effect=lambda sql: sql):
        result = route("list all active floats")

    assert result["source"] == "template"
    assert result["template"]["id"] == "list_active_floats"
