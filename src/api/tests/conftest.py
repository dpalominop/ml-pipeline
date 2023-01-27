"""Pytest fixtures"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope='session', autouse=True)
def client():
    return TestClient(app)