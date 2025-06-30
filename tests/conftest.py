import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def fake_headers():
    return {"Authorization": "Bearer faketoken123"}