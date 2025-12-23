"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.database import init_db, set_db_path
from src.main import app
from src.session import clear_all_sessions


@pytest.fixture(autouse=True)
async def setup_test_database(tmp_path: Path):
    """Set up temporary database for all tests."""
    # Use a temporary file for each test
    db_file = tmp_path / "test_sessions.db"
    set_db_path(db_file)
    await init_db()
    yield
    # Clean up after test
    await clear_all_sessions()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)
