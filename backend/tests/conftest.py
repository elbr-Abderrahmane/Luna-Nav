"""Shared pytest fixtures for LUNA NAV backend tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provide a FastAPI TestClient wired to the LUNA NAV application."""
    return TestClient(app)
