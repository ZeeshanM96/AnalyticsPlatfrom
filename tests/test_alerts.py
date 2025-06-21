import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

FAKE_TOKEN = "Bearer faketoken123"

def test_get_critical_alerts_unauthorized():
    response = client.get("/getalertstatus")
    assert response.status_code == 403 or response.status_code == 401

def test_get_critical_alerts_with_fake_token():
    headers = {"Authorization": FAKE_TOKEN}
    response = client.get("/getalertstatus", headers=headers)
    assert response.status_code == 401 or response.status_code == 403