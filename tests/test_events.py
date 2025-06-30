import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment and setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(dotenv_path=".env.local")

from backend.main import app

client = TestClient(app)
FAKE_TOKEN = "Bearer faketoken123"
fake_headers = {"Authorization": FAKE_TOKEN}
fake_payload = {"user_id": 1}

# ---- Mocks ----

# Generic mock cursor
mock_cursor = MagicMock()
mock_cursor.execute.return_value = None
mock_cursor.fetchone.return_value = (5,)
mock_cursor.fetchall.return_value = [("Login",), ("Logout",)]

mock_conn = MagicMock()
mock_conn.cursor.return_value = mock_cursor
mock_conn.close = MagicMock()

# Trends mock
mock_cursor_trends = MagicMock()
mock_cursor_trends.execute.return_value = None
mock_cursor_trends.fetchone.return_value = (5,)
mock_cursor_trends.fetchall.return_value = [(date(2024, 1, 1), "Login", 10)]

mock_conn_trends = MagicMock()
mock_conn_trends.cursor.return_value = mock_cursor_trends
mock_conn_trends.close = MagicMock()

# Batch mock
mock_cursor_batch = MagicMock()
mock_cursor_batch.execute.return_value = None
mock_cursor_batch.fetchone.return_value = (5,)
mock_cursor_batch.fetchall.return_value = [(date.today(), 3), (date.today(), 5)]

mock_conn_batch = MagicMock()
mock_conn_batch.cursor.return_value = mock_cursor_batch
mock_conn_batch.close = MagicMock()

# ---- Tests ----

@patch("injestion.external_ingest.get_redis_client", return_value=True)
@patch("backend.api.events.decode_jwt_token", return_value=fake_payload)
@patch("backend.api.events.get_connection", return_value=mock_conn)
@patch("backend.api.events.is_admin", return_value=False)
def test_get_event_types(mock_admin, mock_conn_func, mock_jwt, mock_redis):
    response = client.get("/geteventtypes", headers=fake_headers)
    assert response.status_code == 200
    assert response.json() == {"eventTypes": ["Login", "Logout"]}

@patch("injestion.external_ingest.get_redis_client", return_value=True)
@patch("backend.api.events.decode_jwt_token", return_value=fake_payload)
@patch("backend.api.events.get_connection", return_value=mock_conn_trends)
@patch("backend.api.events.is_admin", return_value=False)
@patch("backend.api.events.validate_date_range", return_value=None)
@patch("backend.api.events.fetch_event_summary", return_value=[(date(2024, 1, 1), "Login", 10)])
def test_get_event_trends_success(mock_fetch, mock_validate, mock_admin, mock_conn_func, mock_jwt, mock_redis):
    response = client.get(
        "/geteventtrends/?from_date=2024-01-01&to_date=2024-01-02&events=Login",
        headers=fake_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert "labels" in body
    assert "datasets" in body

@patch("injestion.external_ingest.get_redis_client", return_value=True)
@patch("backend.api.events.decode_jwt_token", return_value=fake_payload)
@patch("backend.api.events.get_connection", return_value=mock_conn_batch)
def test_get_batch_status(mock_conn_func, mock_jwt, mock_redis):
    response = client.get("/getbatchstatus", headers=fake_headers)
    assert response.status_code == 200
    body = response.json()
    assert "today" in body
    assert "yesterday" in body
