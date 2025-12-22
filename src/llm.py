"""LLM integration for content generation."""

import json
from typing import Protocol

import anthropic

from src.components.slides import SlideContent
from src.config import settings


class LLMProvider(Protocol):
    """Protocol for LLM providers to enable testing."""

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Generate a list of slide titles for the topic."""
        ...

    def generate_slide_content(
        self, topic: str, slide_title: str, slide_index: int
    ) -> SlideContent:
        """Generate content for a specific slide."""
        ...

    def simplify_content(self, content: SlideContent) -> SlideContent:
        """Simplify the content for a beginner audience."""
        ...


class AnthropicProvider:
    """Anthropic Claude-based LLM provider."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Generate a list of 5-7 slide titles for the topic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Create a lecture outline for the topic: "{topic}"

Generate exactly 6 slide titles that would form a coherent educational presentation.
The first slide should be an introduction and the last should be a summary/conclusion.

Return ONLY a JSON array of strings, no other text. Example:
["Introduction to Topic", "Core Concept 1", "Core Concept 2", "Advanced Topic", "Practical Applications", "Summary and Next Steps"]""",
                }
            ],
        )
        content = response.content[0].text.strip()
        return json.loads(content)

    def generate_slide_content(
        self, topic: str, slide_title: str, slide_index: int
    ) -> SlideContent:
        """Generate content for a specific slide."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are creating slide {slide_index + 1} of a lecture on "{topic}".
The slide title is: "{slide_title}"

Generate educational content for this slide. Return ONLY a JSON object with these fields:
- "title": The slide title (use the one provided)
- "text": 2-4 sentences explaining the key concepts for this slide. Be clear and educational.

Example:
{{"title": "Introduction to Memory Safety", "text": "Memory safety prevents common programming errors like buffer overflows and use-after-free bugs. These errors can lead to security vulnerabilities and crashes. Modern languages like Rust enforce memory safety at compile time."}}""",
                }
            ],
        )
        content = response.content[0].text.strip()
        data = json.loads(content)
        return SlideContent(title=data["title"], text=data["text"])

    def simplify_content(self, content: SlideContent) -> SlideContent:
        """Simplify the content for a beginner audience."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Rewrite this educational content for a complete beginner (5th grade reading level).
Keep the same core concepts but use simpler words and shorter sentences.
Add a simple analogy if helpful.

Original title: {content.title}
Original text: {content.text}

Return ONLY a JSON object with "title" and "text" fields. Keep the title similar but the text much simpler.""",
                }
            ],
        )
        response_content = response.content[0].text.strip()
        data = json.loads(response_content)
        return SlideContent(title=data["title"], text=data["text"])


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def generate_lecture_outline(self, topic: str) -> list[str]:
        """Return mock slide titles."""
        return [
            f"Introduction to {topic}",
            f"Core Concepts of {topic}",
            "Key Principles",
            "Practical Applications",
            "Common Challenges",
            "Summary and Next Steps",
        ]

    def generate_slide_content(
        self, topic: str, slide_title: str, slide_index: int
    ) -> SlideContent:
        """Return mock slide content."""
        return SlideContent(
            title=slide_title,
            text=f"This is the content for slide {slide_index + 1} about {topic}. "
            f"Here we explore {slide_title.lower()} in detail.",
        )

    def simplify_content(self, content: SlideContent) -> SlideContent:
        """Return simplified mock content."""
        return SlideContent(
            title=f"{content.title} (Simplified)",
            text=f"Simple version: {content.text[:50]}...",
        )


def get_llm_provider(use_mock: bool = False) -> LLMProvider:
    """Get the appropriate LLM provider."""
    if use_mock or not settings.anthropic_api_key:
        return MockLLMProvider()
    return AnthropicProvider()
