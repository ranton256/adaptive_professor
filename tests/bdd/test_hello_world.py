"""BDD tests for hello world feature."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

from src.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def context() -> dict:
    """Shared context between steps."""
    return {}


@scenario("../../features/hello_world.feature", "Backend health check")
def test_backend_health_check() -> None:
    """Test the backend health check scenario."""


@given("the backend server is running")
def backend_running(test_client: TestClient) -> None:
    """Backend server is available via test client."""
    # TestClient handles this - the app is testable
    pass


@when("I request the health endpoint")
def request_health(test_client: TestClient, context: dict) -> None:
    """Request the health endpoint."""
    context["response"] = test_client.get("/health")


@then("I should receive a 200 OK response")
def check_200_response(context: dict) -> None:
    """Verify 200 status code."""
    assert context["response"].status_code == 200


@then(parsers.parse('the response should contain "{key}": "{value}"'))
def check_response_contains(context: dict, key: str, value: str) -> None:
    """Verify response contains expected key-value pair."""
    data = context["response"].json()
    assert data.get(key) == value
