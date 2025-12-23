"""Tests for URL validation utilities."""

import pytest

from src.url_validator import (
    URLCheckResult,
    ValidationResult,
    extract_urls_from_markdown,
    remove_invalid_links_from_markdown,
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


class TestRemoveInvalidLinksFromMarkdown:
    """Tests for remove_invalid_links_from_markdown function."""

    def test_keeps_valid_links(self):
        """Should preserve links that are in the valid set."""
        text = "Check out [Python](https://python.org) for more."
        valid_urls = {"https://python.org"}
        result = remove_invalid_links_from_markdown(text, valid_urls)
        assert "[Python](https://python.org)" in result

    def test_removes_invalid_links_completely(self):
        """Should completely remove lines with invalid links."""
        text = """### Resources
- [Good Link](https://good.com) - Description
- [Bad Link](https://bad.com) - Description
- [Another Good](https://good2.com) - Description"""
        valid_urls = {"https://good.com", "https://good2.com"}
        result = remove_invalid_links_from_markdown(text, valid_urls)
        assert "Good Link" in result
        assert "Another Good" in result
        assert "Bad Link" not in result
        assert "bad.com" not in result

    def test_removes_empty_sections(self):
        """Should remove section headers that have no valid links."""
        text = """### Good Section
- [Valid](https://valid.com) - Works

### Empty Section
- [Bad1](https://bad1.com) - Broken
- [Bad2](https://bad2.com) - Also broken

### Another Good
- [Valid2](https://valid2.com) - Works"""
        valid_urls = {"https://valid.com", "https://valid2.com"}
        result = remove_invalid_links_from_markdown(text, valid_urls)
        assert "Good Section" in result
        assert "Another Good" in result
        assert "Empty Section" not in result
        assert "bad1.com" not in result
        assert "bad2.com" not in result

    def test_mixed_valid_and_invalid(self):
        """Should handle mix of valid and invalid links in same section."""
        text = """### Resources
- [Good](https://good.com) - Valid
- [Bad](https://bad.com) - Invalid
- [Good2](https://good2.com) - Valid"""
        valid_urls = {"https://good.com", "https://good2.com"}
        result = remove_invalid_links_from_markdown(text, valid_urls)
        assert "[Good](https://good.com)" in result
        assert "[Good2](https://good2.com)" in result
        assert "bad.com" not in result


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


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_needs_regeneration_when_few_valid(self):
        """Should flag regeneration when too few valid links."""
        result = ValidationResult(
            filtered_text="text",
            total_links=10,
            valid_links=2,
            needs_regeneration=True,
        )
        assert result.needs_regeneration

    def test_no_regeneration_when_enough_valid(self):
        """Should not flag regeneration when enough valid links."""
        result = ValidationResult(
            filtered_text="text",
            total_links=10,
            valid_links=8,
            needs_regeneration=False,
        )
        assert not result.needs_regeneration


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


class TestValidateAndFilterReferences:
    """Tests for validate_and_filter_references function."""

    @pytest.mark.asyncio
    async def test_returns_validation_result(self):
        """Should return a ValidationResult object."""
        from src.url_validator import validate_and_filter_references

        # Use a simple text without links
        result = await validate_and_filter_references("No links here")
        assert isinstance(result, ValidationResult)
        assert result.total_links == 0
        assert result.valid_links == 0
        assert not result.needs_regeneration

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_flags_regeneration_for_mostly_bad_links(self):
        """Should flag regeneration when most links are invalid."""
        from src.url_validator import validate_and_filter_references

        text = """### Resources
- [Bad1](https://fake-domain-12345.com) - Broken
- [Bad2](https://another-fake-98765.com) - Broken
- [Wikipedia](https://en.wikipedia.org/wiki/Python) - Valid"""

        result = await validate_and_filter_references(text, min_valid_ratio=0.5, min_valid_links=2)
        # Only 1 valid out of 3 = 33%, below 50% threshold
        assert result.needs_regeneration
