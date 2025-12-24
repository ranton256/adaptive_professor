"""Test A2UI compliance of the backend using mock LLMs."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.llm import MockLLMProvider
from src.main import app, set_llm_provider


@pytest.fixture
def mock_llm():
    """Inject a mock LLM provider."""
    provider = MockLLMProvider()
    set_llm_provider(provider)
    return provider


@pytest.mark.asyncio
async def test_start_lecture_returns_a2ui_format(mock_llm):
    """Verify start lecture endpoint returns valid A2UI JSON structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/lecture/start", json={"topic": "Rust Ownership"})

    assert response.status_code == 200
    data = response.json()

    # Check A2UI Root Structure
    assert data["type"] == "render"
    assert "root" in data
    assert "meta" in data

    # Check Meta
    assert data["meta"]["slide_index"] == 0
    assert "session_id" in data["meta"]

    # Check Root Component (should be Container)
    root = data["root"]
    assert root["type"] == "container"
    assert root["layout"] == "vertical"
    assert len(root["children"]) >= 2  # Title + Content at least

    # Check children types
    title_comp = root["children"][0]
    assert title_comp["type"] == "text"
    assert title_comp["variant"] == "h2"

    content_comp = root["children"][1]
    assert content_comp["type"] == "markdown"
