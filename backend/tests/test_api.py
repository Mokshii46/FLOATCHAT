"""API integration tests using TestClient (no real DB or LLM needed)."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Patch heavy startup tasks so TestClient works without Postgres/LLM
    with (
        patch("database.init_db"),
        patch("vectorstore.embed_metadata.embed_schema_docs_if_empty"),
        patch("etl.scheduler.start_scheduler"),
    ):
        from main import app
        with TestClient(app) as c:
            yield c


# ── Health ─────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ── Query endpoint ─────────────────────────────────────────────────

def test_query_rejects_drop(client):
    resp = client.post("/query", json={"sql": "DROP TABLE float_metadata"})
    assert resp.status_code == 400


def test_query_valid_select(client):
    mock_rows = [{"wmo_id": "2902183", "status": "active"}]
    with patch("api.query.execute_query", return_value=mock_rows):
        resp = client.post(
            "/query",
            json={"sql": "SELECT wmo_id, status FROM float_metadata LIMIT 10"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_count"] == 1


# ── Chat endpoint ──────────────────────────────────────────────────

def test_chat_returns_answer(client):
    mock_result = {
        "answer": "The Arabian Sea has an average temperature of 28°C.",
        "viz": {"viz_type": "timeseries", "data": {}, "row_count": 12},
        "anomaly": None,
        "explainability": {"source": "template", "sql": "SELECT 1"},
        "mode_config": {"mode": "citizen"},
        "language": "en",
        "row_count": 12,
    }
    with patch("services.chat_service.process_chat", return_value=mock_result):
        resp = client.post("/chat", json={"question": "Temperature in Arabian Sea?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


def test_chat_empty_question_rejected(client):
    resp = client.post("/chat", json={"question": ""})
    assert resp.status_code == 422


# ── Floats endpoint ────────────────────────────────────────────────

def test_floats_list(client):
    mock_fm = MagicMock()
    mock_fm.wmo_id = "2902183"
    mock_fm.dac = "incois"
    mock_fm.platform_type = "APEX"
    mock_fm.deploy_date = None
    mock_fm.deploy_lat = 12.5
    mock_fm.deploy_lon = 72.3
    mock_fm.is_bgc = False
    mock_fm.status = "active"

    with patch("api.floats.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_fm]
        resp = client.get("/floats")
    assert resp.status_code == 200
