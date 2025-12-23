"""Tests for URL validation utilities."""

import pytest

from src.url_validator import (
    URLCheckResult,
    extract_urls_from_markdown,
    filter_valid_urls_in_markdown,
)


class TestExtractUrlsFromMarkdown:
    """Tests for extract_urls_from_markdown function."""

    def test_extracts_markdown_links(self):
        """Should extract URLs from markdown link syntax."""
        text = "Check out [Python docs](https://docs.python.org) for more info."
        urls = extract_urls_from_markdown(text)
        assert urls == ["https://docs.python.org"]

    def test_extracts_multiple_links(self):
        """Should extract multiple URLs."""
        text = """
        - [Python](https://python.org)
        - [Rust](https://rust-lang.org)
        - [Go](https://go.dev)
        """
        urls = extract_urls_from_markdown(text)
        assert len(urls) == 3
        assert "https://python.org" in urls
        assert "https://rust-lang.org" in urls
        assert "https://go.dev" in urls

    def test_ignores_non_http_links(self):
        """Should ignore non-HTTP links like mailto or relative."""
        text = """
        - [Email](mailto:test@example.com)
        - [Local](/path/to/file)
        - [Valid](https://example.com)
        """
        urls = extract_urls_from_markdown(text)
        assert urls == ["https://example.com"]

    def test_empty_text_returns_empty_list(self):
        """Should return empty list for text without links."""
        urls = extract_urls_from_markdown("No links here!")
        assert urls == []

    def test_handles_urls_with_paths_and_params(self):
        """Should handle complex URLs with paths and query params."""
        text = "[Docs](https://docs.example.com/api/v2?param=value#section)"
        urls = extract_urls_from_markdown(text)
        assert urls == ["https://docs.example.com/api/v2?param=value#section"]


class TestFilterValidUrlsInMarkdown:
    """Tests for filter_valid_urls_in_markdown function."""

    def test_keeps_valid_links(self):
        """Should preserve links that are in the valid set."""
        text = "Check out [Python](https://python.org) for more."
        valid_urls = {"https://python.org"}
        result = filter_valid_urls_in_markdown(text, valid_urls)
        assert "[Python](https://python.org)" in result

    def test_removes_invalid_links(self):
        """Should mark invalid links as unavailable."""
        text = "Check out [Bad Link](https://fake-domain-12345.com) for more."
        valid_urls = set()  # No valid URLs
        result = filter_valid_urls_in_markdown(text, valid_urls)
        assert "https://fake-domain-12345.com" not in result
        assert "~~Bad Link~~" in result
        assert "(link unavailable)" in result

    def test_mixed_valid_and_invalid(self):
        """Should handle mix of valid and invalid links."""
        text = """
        - [Good](https://good.com)
        - [Bad](https://bad.com)
        """
        valid_urls = {"https://good.com"}
        result = filter_valid_urls_in_markdown(text, valid_urls)
        assert "[Good](https://good.com)" in result
        assert "~~Bad~~" in result
        assert "https://bad.com" not in result


class TestURLCheckResult:
    """Tests for URLCheckResult dataclass."""

    def test_valid_result(self):
        """Should create valid result."""
        result = URLCheckResult(url="https://example.com", is_valid=True, status_code=200)
        assert result.is_valid
        assert result.status_code == 200
        assert result.error is None

    def test_invalid_result_with_error(self):
        """Should create invalid result with error."""
        result = URLCheckResult(url="https://fake.com", is_valid=False, error="Connection failed")
        assert not result.is_valid
        assert result.error == "Connection failed"


# Integration tests that actually make HTTP requests
class TestValidateUrlsIntegration:
    """Integration tests that make real HTTP requests.

    These tests are marked as slow and can be skipped with -m "not slow".
    """

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_validates_real_url(self):
        """Should validate a real, known-good URL."""
        from src.url_validator import validate_urls

        results = await validate_urls(["https://www.google.com"])
        assert len(results) == 1
        assert results[0].is_valid

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_detects_fake_url(self):
        """Should detect a fake/non-existent URL."""
        from src.url_validator import validate_urls

        results = await validate_urls(["https://this-domain-definitely-does-not-exist-12345.com"])
        assert len(results) == 1
        assert not results[0].is_valid
