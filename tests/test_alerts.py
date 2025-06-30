import sys
import os
from dotenv import load_dotenv

# Set up environment and sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(dotenv_path=".env.local")

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app

client = TestClient(app)
FAKE_TOKEN = "Bearer faketoken123"
fake_headers = {"Authorization": FAKE_TOKEN}

# ---- Tests ----

@patch("injestion.external_ingest.get_redis_client", return_value=True)
def test_get_critical_alerts_unauthorized(mock_redis):
    """
    Should return 401 or 403 if no auth header is provided.
    """
    response = client.get("/getalertstatus")
    assert response.status_code in (401, 403)


@patch("injestion.external_ingest.get_redis_client", return_value=True)
@patch("backend.api.alerts.decode_jwt_token", return_value=None)
def test_get_critical_alerts_with_fake_token(mock_jwt, mock_redis):
    """
    Should return 401 or 403 for invalid/fake token.
    """
    response = client.get("/getalertstatus", headers=fake_headers)
    assert response.status_code in (401, 403)
