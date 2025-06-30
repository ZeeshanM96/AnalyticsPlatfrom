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
    """
    Provides a pytest fixture that returns a FastAPI TestClient instance for the application.
    
    Returns:
        TestClient: A test client for simulating HTTP requests to the FastAPI app during tests.
    """
    return TestClient(app)

@pytest.fixture
def fake_headers():
    """
    Return a dictionary containing a fake Authorization header with a bearer token for testing purposes.
    
    Returns:
        dict: A dictionary with an Authorization header set to a mock bearer token.
    """
    return {"Authorization": "Bearer faketoken123"}