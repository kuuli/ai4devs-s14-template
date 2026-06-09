import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-a-real-key")

import pytest
from fastapi.testclient import TestClient

from main import app, _store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_session_store():
    _store.clear()
    yield
    _store.clear()
