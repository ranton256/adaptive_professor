"""URL validation utilities for checking link validity."""

import asyncio
import re
from dataclasses import dataclass

import httpx


@dataclass
class URLCheckResult:
    """Result of checking a URL."""

    url: str
    is_valid: bool
    status_code: int | None = None
    error: str | None = None


# Common URL patterns that are known to be valid (official docs, etc.)
# These are checked less aggressively to avoid rate limiting
TRUSTED_DOMAINS = {
    "docs.python.org",
    "developer.mozilla.org",
    "en.wikipedia.org",
    "github.com",
    "stackoverflow.com",
    "rust-lang.org",
    "doc.rust-lang.org",
    "crates.io",
    "reactjs.org",
    "react.dev",
    "nodejs.org",
    "npmjs.com",
    "pypi.org",
    "arxiv.org",
    "doi.org",
    "youtube.com",
    "www.youtube.com",
}


def extract_urls_from_markdown(text: str) -> list[str]:
    """Extract all URLs from markdown text.

    Handles both:
    - [link text](url)
    - bare URLs
    """
    # Pattern for markdown links: [text](url)
    markdown_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    urls = []

    for match in re.finditer(markdown_link_pattern, text):
        url = match.group(2)
        if url.startswith("http"):
            urls.append(url)

    return urls


async def check_url(
    client: httpx.AsyncClient,
    url: str,
    timeout: float = 10.0,
) -> URLCheckResult:
    """Check if a URL is valid by making a HEAD request.

    Falls back to GET if HEAD is not allowed.
    """
    # Extract domain for trusted domain check
    try:
        domain = url.split("//")[1].split("/")[0]
        if domain.startswith("www."):
            domain_check = domain[4:]
        else:
            domain_check = domain
    except IndexError:
        return URLCheckResult(url=url, is_valid=False, error="Invalid URL format")

    # For trusted domains, we can be more lenient
    is_trusted = domain_check in TRUSTED_DOMAINS or domain in TRUSTED_DOMAINS

    try:
        # Try HEAD first (faster, less bandwidth)
        response = await client.head(
            url,
            timeout=timeout,
            follow_redirects=True,
        )

        # Accept 2xx and 3xx as valid
        if response.status_code < 400:
            return URLCheckResult(url=url, is_valid=True, status_code=response.status_code)

        # If HEAD returns 405 (Method Not Allowed), try GET
        if response.status_code == 405:
            response = await client.get(
                url,
                timeout=timeout,
                follow_redirects=True,
            )
            if response.status_code < 400:
                return URLCheckResult(url=url, is_valid=True, status_code=response.status_code)

        return URLCheckResult(url=url, is_valid=False, status_code=response.status_code)

    except httpx.TimeoutException:
        # Trusted domains get benefit of the doubt on timeout
        if is_trusted:
            return URLCheckResult(url=url, is_valid=True, error="Timeout (trusted domain)")
        return URLCheckResult(url=url, is_valid=False, error="Timeout")

    except httpx.ConnectError:
        return URLCheckResult(url=url, is_valid=False, error="Connection failed")

    except httpx.TooManyRedirects:
        return URLCheckResult(url=url, is_valid=False, error="Too many redirects")

    except Exception as e:
        return URLCheckResult(url=url, is_valid=False, error=str(e)[:100])


async def validate_urls(
    urls: list[str],
    timeout: float = 10.0,
    max_concurrent: int = 5,
) -> list[URLCheckResult]:
    """Validate multiple URLs concurrently.

    Args:
        urls: List of URLs to check
        timeout: Timeout per request in seconds
        max_concurrent: Maximum concurrent requests

    Returns:
        List of URLCheckResult for each URL
    """
    if not urls:
        return []

    # Create a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_with_semaphore(client: httpx.AsyncClient, url: str) -> URLCheckResult:
        async with semaphore:
            return await check_url(client, url, timeout)

    # Use a single client for connection pooling
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AdaptiveProfessor/1.0; +educational)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [check_with_semaphore(client, url) for url in urls]
        results = await asyncio.gather(*tasks)

    return list(results)


def remove_invalid_links_from_markdown(text: str, valid_urls: set[str]) -> str:
    """Remove lines containing invalid URLs from markdown text.

    Completely removes list items with broken links and cleans up empty sections.
    """
    lines = text.split("\n")

    # Pattern for markdown links: [text](url)
    markdown_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    # First pass: mark lines to keep/remove
    keep_line = []
    for line in lines:
        match = re.search(markdown_link_pattern, line)
        if match:
            url = match.group(2)
            if url.startswith("http") and url not in valid_urls:
                # Remove this line - it has a broken link
                keep_line.append(False)
            else:
                # Valid link or non-http link, keep it
                keep_line.append(True)
        else:
            # No link in this line, keep it for now
            keep_line.append(True)

    # Second pass: remove headers that have no content after them
    final_keep = keep_line.copy()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("#"):
            # This is a header - check if it has any content before the next header
            has_content = False
            j = i + 1
            while j < len(lines):
                if lines[j].strip().startswith("#"):
                    # Hit another header
                    break
                if keep_line[j] and lines[j].strip():
                    # Found non-empty content that we're keeping
                    has_content = True
                    break
                j += 1

            if not has_content:
                # Mark this header for removal
                final_keep[i] = False
        i += 1

    # Build result, filtering out removed lines
    result_lines = []
    for i, line in enumerate(lines):
        if final_keep[i]:
            result_lines.append(line)

    # Clean up multiple consecutive blank lines
    cleaned_lines = []
    prev_blank = False
    for line in result_lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        cleaned_lines.append(line)
        prev_blank = is_blank

    # Remove trailing blank lines
    while cleaned_lines and cleaned_lines[-1].strip() == "":
        cleaned_lines.pop()

    return "\n".join(cleaned_lines)


@dataclass
class ValidationResult:
    """Result of validating references."""

    filtered_text: str
    total_links: int
    valid_links: int
    needs_regeneration: bool


async def validate_and_filter_references(
    markdown_text: str,
    min_valid_ratio: float = 0.5,
    min_valid_links: int = 3,
) -> ValidationResult:
    """Validate all URLs in a markdown references section.

    Args:
        markdown_text: The markdown text containing reference links
        min_valid_ratio: Minimum ratio of valid links to trigger regeneration (default 0.5)
        min_valid_links: Minimum number of valid links required (default 3)

    Returns:
        ValidationResult with filtered text and regeneration flag
    """
    urls = extract_urls_from_markdown(markdown_text)

    if not urls:
        return ValidationResult(
            filtered_text=markdown_text,
            total_links=0,
            valid_links=0,
            needs_regeneration=False,
        )

    results = await validate_urls(urls)

    valid_urls = {r.url for r in results if r.is_valid}
    total = len(urls)
    valid = len(valid_urls)

    # Determine if regeneration is needed
    valid_ratio = valid / total if total > 0 else 0
    needs_regeneration = valid < min_valid_links or valid_ratio < min_valid_ratio

    # Remove invalid links entirely
    filtered_text = remove_invalid_links_from_markdown(markdown_text, valid_urls)

    return ValidationResult(
        filtered_text=filtered_text,
        total_links=total,
        valid_links=valid,
        needs_regeneration=needs_regeneration,
    )
