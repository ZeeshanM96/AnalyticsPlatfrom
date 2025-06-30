import sys
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env.local")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch

client = TestClient(app)
FAKE_TOKEN = "Bearer faketoken123"

@patch("injestion.external_ingest.get_redis_client", return_value=True)
def test_get_critical_alerts_unauthorized(mock_redis):
    response = client.get("/getalertstatus")
    assert response.status_code in (401, 403)

@patch("injestion.external_ingest.get_redis_client", return_value=True)
def test_get_critical_alerts_with_fake_token(mock_redis):
    headers = {"Authorization": FAKE_TOKEN}
    response = client.get("/getalertstatus", headers=headers)
    assert response.status_code in (401, 403)
