from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.local")
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch
from datetime import date

client = TestClient(app)
FAKE_TOKEN = "Bearer faketoken123"
fake_headers = {"Authorization": FAKE_TOKEN}

# Mocks
fake_payload = {"user_id": 1}

mock_cursor = type("Cursor", (), {
    "execute": lambda self, q, p=None: None,
    "fetchone": lambda self: (5,),
    "fetchall": lambda self: [("Login",), ("Logout",)]
})()

mock_conn = type("Conn", (), {"cursor": lambda self: mock_cursor})()

mock_cursor_trends = type("Cursor", (), {
    "execute": lambda self, q, p=None: None,
    "fetchone": lambda self: (5,),
    "fetchall": lambda self: [(date(2024, 1, 1), "Login", 10)]
})()

mock_conn_trends = type("Conn", (), {"cursor": lambda self: mock_cursor_trends})()

mock_cursor_batch = type("Cursor", (), {
    "execute": lambda self, q, p=None: None,
    "fetchone": lambda self: (5,),
    "fetchall": lambda self: [(date.today(), 3), (date.today(), 5)]
})()

mock_conn_batch = type("Conn", (), {"cursor": lambda self: mock_cursor_batch})()

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
def test_get_event_trends_success(mock_validate, mock_admin, mock_conn_func, mock_jwt, mock_redis):
    """
    Test the /geteventtrends endpoint for successful retrieval of event trend data.
    
    Sends a GET request with date range and event type parameters, asserting a 200 response and that the JSON contains 'labels' and 'datasets' keys.
    """
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
    """
    Tests the /getbatchstatus endpoint for successful retrieval of batch status data.
    
    Sends a GET request to the endpoint and verifies that the response contains the expected keys for "today" and "yesterday".
    """
    response = client.get("/getbatchstatus", headers=fake_headers)
    assert response.status_code == 200
    body = response.json()
    assert "today" in body
    assert "yesterday" in body
