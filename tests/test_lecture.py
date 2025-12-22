"""Tests for lecture endpoints."""

from fastapi.testclient import TestClient


def test_start_lecture_returns_slide(client: TestClient) -> None:
    """Starting a lecture should return a slide payload."""
    response = client.post("/api/lecture/start", json={"topic": "Test Topic"})
    assert response.status_code == 200


def test_start_lecture_includes_topic_in_title(client: TestClient) -> None:
    """The first slide title should include the requested topic."""
    response = client.post("/api/lecture/start", json={"topic": "Rust Ownership"})
    data = response.json()
    assert "Rust Ownership" in data["content"]["title"]


def test_start_lecture_includes_interactive_controls(client: TestClient) -> None:
    """The first slide should include interactive controls."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    assert len(data["interactive_controls"]) > 0


def test_start_lecture_has_next_button(client: TestClient) -> None:
    """The first slide should have a Next button."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    assert "Next" in labels
