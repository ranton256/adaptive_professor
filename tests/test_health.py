"""Tests for health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient) -> None:
    """Health endpoint should return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_returns_healthy_status(client: TestClient) -> None:
    """Health endpoint should return healthy status."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


def test_health_check_returns_service_name(client: TestClient) -> None:
    """Health endpoint should return service name."""
    response = client.get("/health")
    data = response.json()
    assert data["service"] == "Adaptive Professor"
