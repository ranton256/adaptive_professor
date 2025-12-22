"""Tests for lecture endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.llm import MockLLMProvider
from src.main import app, set_llm_provider
from src.session import clear_all_sessions


@pytest.fixture(autouse=True)
def setup_mock_llm():
    """Use mock LLM provider for all tests."""
    set_llm_provider(MockLLMProvider())
    clear_all_sessions()
    yield
    clear_all_sessions()


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_start_lecture_returns_slide(client: TestClient) -> None:
    """Starting a lecture should return a slide payload."""
    response = client.post("/api/lecture/start", json={"topic": "Test Topic"})
    assert response.status_code == 200


def test_start_lecture_includes_session_id(client: TestClient) -> None:
    """The response should include a session ID."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    assert "session_id" in data
    assert data["session_id"] is not None


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


def test_start_lecture_includes_slide_progress(client: TestClient) -> None:
    """The response should include slide index and total."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    assert data["slide_index"] == 0
    assert data["total_slides"] > 1


def test_action_advance_returns_next_slide(client: TestClient) -> None:
    """Advancing should return the next slide."""
    # Start lecture
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    # Advance to next slide
    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "advance_main_thread"},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    assert data["slide_index"] == 1


def test_action_advance_generates_content(client: TestClient) -> None:
    """Advancing should generate content for the new slide."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "advance_main_thread"},
    )

    data = action_response.json()
    assert data["content"]["title"] is not None
    assert data["content"]["text"] is not None


def test_action_previous_returns_previous_slide(client: TestClient) -> None:
    """Going previous should return the previous slide."""
    # Start and advance
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "advance_main_thread"},
    )

    # Go back
    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "go_previous"},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    assert data["slide_index"] == 0


def test_action_simplify_returns_simplified_content(client: TestClient) -> None:
    """Simplifying should return modified content."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "simplify_slide"},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    # Mock provider adds "(Simplified)" to title
    assert "Simplified" in data["content"]["title"]


def test_action_invalid_session_returns_404(client: TestClient) -> None:
    """Actions on invalid session should return 404."""
    response = client.post(
        "/api/lecture/invalid-session/action",
        json={"action": "advance_main_thread"},
    )
    assert response.status_code == 404


def test_action_unknown_action_returns_400(client: TestClient) -> None:
    """Unknown actions should return 400."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "unknown_action"},
    )
    assert response.status_code == 400


def test_action_advance_past_end_returns_400(client: TestClient) -> None:
    """Advancing past the last slide should return 400."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]
    total_slides = start_response.json()["total_slides"]

    # Advance to the end
    for _ in range(total_slides - 1):
        client.post(
            f"/api/lecture/{session_id}/action",
            json={"action": "advance_main_thread"},
        )

    # Try to advance past end
    response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "advance_main_thread"},
    )
    assert response.status_code == 400


def test_action_previous_at_start_returns_400(client: TestClient) -> None:
    """Going previous at first slide should return 400."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "go_previous"},
    )
    assert response.status_code == 400


def test_first_slide_has_no_previous_button(client: TestClient) -> None:
    """First slide should not have a Previous button."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    assert "Previous" not in labels


def test_second_slide_has_previous_button(client: TestClient) -> None:
    """Second slide should have a Previous button."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "advance_main_thread"},
    )

    data = action_response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    assert "Previous" in labels


def test_last_slide_has_no_next_button(client: TestClient) -> None:
    """Last slide should not have a Next button."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]
    total_slides = start_response.json()["total_slides"]

    # Advance to the end
    for _ in range(total_slides - 1):
        response = client.post(
            f"/api/lecture/{session_id}/action",
            json={"action": "advance_main_thread"},
        )

    data = response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    assert "Next" not in labels
