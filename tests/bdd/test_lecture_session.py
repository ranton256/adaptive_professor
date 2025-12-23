"""BDD tests for lecture session feature."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenario, then, when

from src.llm import MockLLMProvider
from src.main import app, set_llm_provider


@pytest.fixture(autouse=True)
def setup():
    """Setup mock LLM for all tests."""
    set_llm_provider(MockLLMProvider())
    yield


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def context() -> dict:
    """Shared context between steps."""
    return {}


# Scenarios
@scenario("../../features/lecture_session.feature", "Start a lecture from a topic")
def test_start_lecture_from_topic() -> None:
    """Test starting a lecture from a topic."""


@scenario("../../features/lecture_session.feature", "Navigate to next slide")
def test_navigate_to_next_slide() -> None:
    """Test navigating to next slide."""


@scenario("../../features/lecture_session.feature", "Request simplified explanation")
def test_request_simplified_explanation() -> None:
    """Test requesting simplified explanation."""


# Given steps
@given("the backend server is running")
def backend_running(test_client: TestClient) -> None:
    """Backend server is available via test client."""
    pass


@given("the frontend application is running")
def frontend_running() -> None:
    """Frontend is assumed to be running for BDD tests."""
    pass


@given("I am on the home page")
def on_home_page() -> None:
    """User is on the home page."""
    pass


@given(parsers.parse('I have started a lecture on "{topic}"'))
def started_lecture(test_client: TestClient, context: dict, topic: str) -> None:
    """Start a lecture on the given topic."""
    response = test_client.post("/api/lecture/start", json={"topic": topic})
    assert response.status_code == 200
    context["response"] = response
    context["slide"] = response.json()
    context["session_id"] = response.json()["session_id"]


@given("I am viewing a slide")
def viewing_slide(context: dict) -> None:
    """User is viewing a slide."""
    assert context.get("slide") is not None


@given("I am viewing a slide with technical content")
def viewing_technical_slide(context: dict) -> None:
    """User is viewing a slide with technical content."""
    assert context.get("slide") is not None
    assert context["slide"]["content"]["text"] is not None


# When steps
@when(parsers.parse('I enter the topic "{topic}"'))
def enter_topic(context: dict, topic: str) -> None:
    """Enter a topic."""
    context["topic"] = topic


@when('I click "Start Lecture"')
def click_start_lecture(test_client: TestClient, context: dict) -> None:
    """Click start lecture button."""
    topic = context.get("topic", "Test Topic")
    response = test_client.post("/api/lecture/start", json={"topic": topic})
    context["response"] = response
    if response.status_code == 200:
        context["slide"] = response.json()
        context["session_id"] = response.json()["session_id"]


@when('I click the "Next" button')
def click_next(test_client: TestClient, context: dict) -> None:
    """Click the Next button."""
    session_id = context["session_id"]
    response = test_client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "advance_main_thread"},
    )
    context["response"] = response
    if response.status_code == 200:
        context["previous_slide"] = context["slide"]
        context["slide"] = response.json()


@when('I click the "Simplify" button')
def click_simplify(test_client: TestClient, context: dict) -> None:
    """Click the Simplify button."""
    session_id = context["session_id"]
    context["original_slide"] = context["slide"]
    response = test_client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "simplify_slide"},
    )
    context["response"] = response
    if response.status_code == 200:
        context["slide"] = response.json()


# Then steps
@then("I should see the first slide rendered")
def see_first_slide(context: dict) -> None:
    """Verify first slide is rendered."""
    assert context["response"].status_code == 200
    assert context["slide"]["slide_index"] == 0


@then("the slide should have a title")
def slide_has_title(context: dict) -> None:
    """Verify slide has a title."""
    assert context["slide"]["content"]["title"] is not None
    assert len(context["slide"]["content"]["title"]) > 0


@then("I should see navigation options")
def see_navigation_options(context: dict) -> None:
    """Verify navigation options are present."""
    controls = context["slide"]["interactive_controls"]
    assert len(controls) > 0
    labels = [c["label"] for c in controls]
    # Dynamic A2UI: buttons have contextual labels like "Next: Topic" or "Simplify This"
    has_next = any("Next" in label for label in labels)
    has_simplify = any("Simplify" in label for label in labels)
    assert has_next or has_simplify


@then("I should see the next slide in the main thread")
def see_next_slide(context: dict) -> None:
    """Verify we're on the next slide."""
    assert context["response"].status_code == 200
    assert context["slide"]["slide_index"] == context["previous_slide"]["slide_index"] + 1


@then("the slide transition should be smooth")
def smooth_transition(context: dict) -> None:
    """Verify slide transition (in API context, just verify response is quick)."""
    # This is more of a frontend concern; in API tests we just verify success
    assert context["response"].status_code == 200


@then("the current slide should be rewritten")
def slide_rewritten(context: dict) -> None:
    """Verify the slide was rewritten."""
    assert context["response"].status_code == 200
    # The slide content should be different after simplification
    original_title = context["original_slide"]["content"]["title"]
    new_title = context["slide"]["content"]["title"]
    # Mock provider adds "(Simplified)" to title
    assert new_title != original_title or "Simplified" in new_title


@then("the language should be appropriate for a beginner")
def beginner_language(context: dict) -> None:
    """Verify simplified language."""
    # Mock provider adds "(Simplified)" indicator
    assert "Simplified" in context["slide"]["content"]["title"]


@then("the core concepts should remain the same")
def core_concepts_remain(context: dict) -> None:
    """Verify core concepts are preserved."""
    # The slide should still have content
    assert len(context["slide"]["content"]["text"]) > 0
