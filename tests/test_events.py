# tests/test_events.py

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

FAKE_TOKEN = "Bearer faketoken123"

def test_get_event_types_unauthorized():
    response = client.get("/geteventtypes")
    assert response.status_code in (401, 403)

def test_get_event_trends_no_token():
    response = client.get("/geteventtrends/?from_date=2024-01-01&to_date=2024-01-02&events=Login")
    assert response.status_code == 403 or response.status_code == 401

def test_get_event_trends_missing_event_type():
    headers = {"Authorization": FAKE_TOKEN}
    response = client.get("/geteventtrends/?from_date=2024-01-01&to_date=2024-01-02", headers=headers)
    assert response.status_code == 400  # Missing `events` parameter causes failure

def test_get_batch_status_unauthorized():
    response = client.get("/getbatchstatus")
    assert response.status_code in (401, 403)