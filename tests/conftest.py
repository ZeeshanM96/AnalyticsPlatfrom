import sys
import os
from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Generate a FERNET_KEY if not already set (used for encryption in tests)
if not os.getenv("FERNET_KEY"):
    os.environ["FERNET_KEY"] = Fernet.generate_key().decode()

# Import the FastAPI app after environment is ready
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def fake_headers():
    return {"Authorization": "Bearer faketoken123"}
