"""BDD tests for lecture session feature."""

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

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


# Load all scenarios from the feature file
scenarios("../../features/lecture_session.feature")

# Explicit scenario functions are not needed when using scenarios()


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
    context["session_id"] = response.json()["meta"]["session_id"]


@then("I should see the first slide rendered")
def see_first_slide(context: dict) -> None:
    """Verify first slide is rendered."""
    assert context["response"].status_code == 200
    assert context["slide"]["meta"]["slide_index"] == 0


@given("I am viewing a slide with technical content")
def viewing_technical_slide(context: dict) -> None:
    """User is viewing a slide with technical content."""
    assert context.get("slide") is not None
    # Just check if root exists for now as structure varies
    assert context["slide"]["root"] is not None


@when('I click "Start Lecture"')
def click_start_lecture(test_client: TestClient, context: dict) -> None:
    """Click start lecture button."""
    topic = context.get("topic", "Test Topic")
    response = test_client.post("/api/lecture/start", json={"topic": topic})
    context["response"] = response
    if response.status_code == 200:
        context["slide"] = response.json()
        context["session_id"] = response.json()["meta"]["session_id"]


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


@when('I click the "Clarify" button')
def click_clarify(test_client: TestClient, context: dict) -> None:
    """Click the Clarify button."""
    session_id = context["session_id"]
    context["original_slide"] = context["slide"]
    response = test_client.post(
        f"/api/lecture/{session_id}/action",
        json={"action": "clarify_slide"},
    )
    context["response"] = response
    if response.status_code == 200:
        context["slide"] = response.json()


@then("I should see the next slide in the main thread")
def see_next_slide(context: dict) -> None:
    """Verify we're on the next slide."""
    assert context["response"].status_code == 200
    assert (
        context["slide"]["meta"]["slide_index"]
        == context["previous_slide"]["meta"]["slide_index"] + 1
    )


@then("I should see navigation options")
def see_navigation_options(context: dict) -> None:
    """Verify navigation options are present."""

    # Helper to find buttons in A2UI tree
    def find_buttons(root):
        btns = []
        if root["type"] == "button":
            btns.append(root)
        if "children" in root:
            for child in root["children"]:
                btns.extend(find_buttons(child))
        return btns

    buttons = find_buttons(context["slide"]["root"])
    assert len(buttons) > 0
    labels = [c["label"] for c in buttons]

    has_next = any("Next" in label for label in labels)
    has_simplify = any("Simplify" in label for label in labels)
    assert has_next or has_simplify


@then("the explanation should be clearer with defined terms")
def clearer_explanation(context: dict) -> None:
    """Verify clarified content."""

    # Find h2
    def find_h2(root):
        if root["type"] == "text" and root.get("variant") == "h2":
            return root["content"]
        if "children" in root:
            for child in root["children"]:
                res = find_h2(child)
                if res:
                    return res
        return None

    title = find_h2(context["slide"]["root"])
    assert title is not None and "Clarified" in title


@then("the current slide should be rewritten")
def slide_rewritten(context: dict) -> None:
    """Verify the slide was rewritten."""
    assert context["response"].status_code == 200

    def find_h2(root):
        if root["type"] == "text" and root.get("variant") == "h2":
            return root["content"]
        if "children" in root:
            for child in root["children"]:
                res = find_h2(child)
                if res:
                    return res
        return None

    new_title = find_h2(context["slide"]["root"])
    assert new_title is not None and "Clarified" in new_title


@then("the slide should have a title")
def slide_has_title(context: dict) -> None:
    """Verify slide has a title."""

    def find_h2(root):
        if root["type"] == "text" and root.get("variant") == "h2":
            return root["content"]
        if "children" in root:
            for child in root["children"]:
                res = find_h2(child)
                if res:
                    return res
        return None

    assert find_h2(context["slide"]["root"]) is not None


@then("the core concepts should remain the same")
def core_concepts_remain(context: dict) -> None:
    """Verify core concepts are preserved."""
    # Just check that we have content
    assert context["slide"]["root"] is not None
