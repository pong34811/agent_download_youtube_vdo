"""URL validation and batch preflight for the YouTube downloader."""
from __future__ import annotations

from urllib.parse import urlparse

_VALID_SCHEMES = {"http", "https"}
_VALID_HOSTS = {"youtube.com", "youtu.be"}


def is_valid_youtube_url(url: str) -> bool:
    """Return True if *url* is an HTTP(S) URL on youtube.com or youtu.be."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in _VALID_SCHEMES:
        return False
    netloc = parsed.netloc.lower()
    # Accept exact match or subdomain (e.g. music.youtube.com)
    return netloc in _VALID_HOSTS or netloc.endswith(".youtube.com")


def validate_batch(urls: list[str]) -> tuple[list[str], list[str]]:
    """Validate and deduplicate a list of YouTube URLs.

    Returns ``(unique_valid_urls, error_messages)``.  If *error_messages* is
    non-empty the caller must reject the entire batch before any network call.
    Deduplication preserves input order; the count limit is checked on the
    deduplicated list.
    """
    # Deduplicate preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    errors: list[str] = []

    if not unique:
        errors.append("No URLs provided. Please supply at least one YouTube URL.")
        return [], errors

    if len(unique) > 22:
        errors.append(
            f"Too many URLs: {len(unique)} supplied but the maximum batch size is 22."
        )

    invalid = [u for u in unique if not is_valid_youtube_url(u)]
    for u in invalid:
        errors.append(f"Invalid or non-YouTube URL: {u!r}")

    return unique, errors
