"""Tests for the SQL validator."""

import pytest

from nl2sql.sql_validator import validate, SQLValidationError, _enforce_limit


# ── Valid queries ──────────────────────────────────────────────────

def test_valid_select_passes():
    sql = "SELECT wmo_id FROM float_metadata LIMIT 10;"
    result = validate(sql)
    assert "SELECT" in result.upper()


def test_limit_is_added_when_missing():
    sql = "SELECT wmo_id FROM float_metadata"
    result = validate(sql)
    assert "LIMIT" in result.upper()


def test_existing_limit_capped():
    sql = "SELECT wmo_id FROM float_metadata LIMIT 999999"
    result = validate(sql)
    # Must be capped at max_result_rows (5000)
    assert "LIMIT 5000" in result


# ── Rejected queries ───────────────────────────────────────────────

@pytest.mark.parametrize("bad_sql", [
    "DROP TABLE float_metadata",
    "DELETE FROM profiles WHERE 1=1",
    "UPDATE profiles SET temperature = 0",
    "INSERT INTO float_metadata (wmo_id) VALUES ('999')",
    "TRUNCATE profiles",
    "ALTER TABLE profiles ADD COLUMN foo int",
    "SELECT * FROM float_metadata; DROP TABLE float_metadata",
    "SELECT * FROM pg_catalog.pg_tables",
])
def test_rejects_dangerous_sql(bad_sql: str):
    with pytest.raises(SQLValidationError):
        validate(bad_sql)


def test_rejects_non_select():
    with pytest.raises(SQLValidationError):
        validate("EXEC sp_tables")


# ── _enforce_limit ─────────────────────────────────────────────────

def test_enforce_limit_adds():
    sql = "SELECT 1"
    result = _enforce_limit(sql, 100)
    assert "LIMIT 100" in result

def test_enforce_limit_reduces():
    sql = "SELECT 1 LIMIT 99999"
    result = _enforce_limit(sql, 100)
    assert "LIMIT 100" in result
    assert "99999" not in result
