"""Module that provides utility functions for the Survey Assist API.

This module contains general utility functions used across the API,
including logging helpers for consistent, privacy-preserving identifier truncation.
"""

import hashlib

DEFAULT_TRUNCATE_LEN = 8


def truncate_identifier(value: str | None, max_len: int = DEFAULT_TRUNCATE_LEN) -> str:
    """Return a truncated string safely, handling None and short values.

    Used for logging to preserve privacy while providing enough context.

    Args:
        value (str | None): The string to truncate.
        max_len (int): Maximum length before truncation. Defaults to 8.

    Returns:
        str: Empty string if value is None/empty, otherwise truncated string
            with "..." suffix if longer than max_len.
    """
    if not value:
        return ""
    return value if len(value) <= max_len else value[:max_len] + "..."


def hash_identifier(value: str | None, digest_len: int = 12) -> str:
    """Return a non-reversible short hash for sensitive identifiers.

    Generates a hex-encoded SHA-256 digest and truncates it for logging.
    This preserves traceability across logs without exposing raw content.

    Args:
        value (str | None): The value to hash.
        digest_len (int): Number of hex characters to keep. Defaults to 12.

    Returns:
        str: Empty string if input is None/empty, otherwise truncated hex digest.
    """
    if not value:
        return ""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:digest_len]
