"""Tests for lecture endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.llm import MockLLMProvider
from src.main import set_llm_provider


@pytest.fixture(autouse=True)
def setup_mock_llm():
    """Use mock LLM provider for all tests."""
    set_llm_provider(MockLLMProvider())
    yield


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
    """The first slide should have a Next button (contextual label)."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    # Dynamic A2UI: button label includes next slide topic, e.g., "Next: Core Concepts"
    assert any(label.startswith("Next:") for label in labels)


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
    assert not any("Previous" in label for label in labels)


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
    assert any("Previous" in label for label in labels)


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
    # No "Next:" button on the last slide
    assert not any(label.startswith("Next:") for label in labels)


def test_deep_dive_action_returns_deep_dive_slide(client: TestClient) -> None:
    """Deep dive action should return a deep dive slide."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "deep_dive", "params": {"concept": "ownership"}},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    assert data["layout"] == "deep_dive"
    assert "ownership" in data["content"]["title"].lower()


def test_deep_dive_has_return_button(client: TestClient) -> None:
    """Deep dive slide should have a return button."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "deep_dive", "params": {"concept": "ownership"}},
    )

    data = action_response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    # Should have a "Return to: ..." button
    assert any("Return to:" in label for label in labels)


def test_deep_dive_requires_concept_param(client: TestClient) -> None:
    """Deep dive action requires a concept parameter."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "deep_dive"},  # No params
    )

    assert response.status_code == 400


def test_return_to_main_action(client: TestClient) -> None:
    """Return to main action should exit deep dive."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    # Enter deep dive
    client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "deep_dive", "params": {"concept": "ownership"}},
    )

    # Return to main
    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "return_to_main", "params": {"slide_index": 0}},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    assert data["layout"] == "default"
    assert data["slide_index"] == 0


def test_return_to_main_works_from_example(client: TestClient) -> None:
    """Return to main should work from example slides."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    # Go to example
    client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "show_example"},
    )

    # Return to main
    response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "return_to_main", "params": {"slide_index": 0}},
    )

    assert response.status_code == 200
    assert response.json()["layout"] == "default"


def test_slides_have_contextual_deep_dive_controls(client: TestClient) -> None:
    """Slides should have contextual deep dive options."""
    response = client.post("/api/lecture/start", json={"topic": "Rust"})
    data = response.json()

    # Find controls with deep_dive action
    deep_dive_controls = [c for c in data["interactive_controls"] if c["action"] == "deep_dive"]

    assert len(deep_dive_controls) > 0
    # Deep dive controls should have concept params
    for control in deep_dive_controls:
        assert control.get("params") is not None
        assert "concept" in control["params"]


def test_multiple_examples_then_return(client: TestClient) -> None:
    """Return to main should work after multiple examples."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    # First example
    example1_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "show_example"},
    )
    assert example1_response.status_code == 200
    assert example1_response.json()["session_id"] == session_id

    # Second example (another example)
    example2_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "show_example"},
    )
    assert example2_response.status_code == 200
    assert example2_response.json()["session_id"] == session_id

    # Return to main
    return_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "return_to_main", "params": {"slide_index": 0}},
    )
    assert return_response.status_code == 200
    assert return_response.json()["layout"] == "default"
    assert return_response.json()["session_id"] == session_id


def test_extend_lecture_adds_more_slides(client: TestClient) -> None:
    """Extend lecture action should add more slides and advance."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]
    initial_total = start_response.json()["total_slides"]

    # Advance to the last slide
    for _ in range(initial_total - 1):
        client.post(
            f"/api/lecture/{session_id}/action",
            json={"action": "advance_main_thread"},
        )

    # Extend the lecture
    extend_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "extend_lecture"},
    )

    assert extend_response.status_code == 200
    data = extend_response.json()
    # Should have more slides now
    assert data["total_slides"] > initial_total
    # Should be on a new slide (one past the old last slide)
    assert data["slide_index"] == initial_total


def test_last_slide_has_continue_learning_button(client: TestClient) -> None:
    """Last slide should have a Continue Learning button."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]
    total_slides = start_response.json()["total_slides"]

    # Advance to the last slide
    for _ in range(total_slides - 1):
        response = client.post(
            f"/api/lecture/{session_id}/action",
            json={"action": "advance_main_thread"},
        )

    data = response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    # Should have "Continue Learning" button
    assert any("Continue Learning" in label for label in labels)


def test_show_references_returns_references_slide(client: TestClient) -> None:
    """Show references action should return a references slide."""
    start_response = client.post("/api/lecture/start", json={"topic": "Test"})
    session_id = start_response.json()["session_id"]

    action_response = client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "show_references"},
    )

    assert action_response.status_code == 200
    data = action_response.json()
    assert data["layout"] == "references"
    assert "References" in data["content"]["title"]


def test_slides_have_view_references_button(client: TestClient) -> None:
    """Slides should have a View References button."""
    response = client.post("/api/lecture/start", json={"topic": "Test"})
    data = response.json()
    labels = [c["label"] for c in data["interactive_controls"]]
    assert any("References" in label for label in labels)
