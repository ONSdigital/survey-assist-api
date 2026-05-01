"""Shared request handling for classification lookup endpoints (SIC and SOC).

Both SIC and SOC lookup routes use the same flow: validate description, call
client.get_result, handle not found, log and return. This module holds that
logic so the routes stay thin and duplicate-code lint is avoided.
"""

import time
from typing import Any, Protocol

from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

from utils.survey import truncate_identifier

logger = get_logger(__name__)


class LookupClientProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for lookup clients (SIC or SOC) used by the shared handler."""

    def get_result(self, description: str, similarity: bool) -> dict[str, Any] | None:
        """Return lookup result or None if not found."""
        ...  # pylint: disable=unnecessary-ellipsis


def execute_lookup_request(
    description: str,
    similarity: bool,
    lookup_client: LookupClientProtocol,
    endpoint_name: str,
    code_label: str,
) -> dict[str, Any]:
    """Run a classification lookup request and return the result or raise.

    Args:
        description: The description to look up.
        similarity: Whether to use similarity search.
        lookup_client: Client with get_result(description, similarity).
        endpoint_name: Label for logs (e.g. "sic-lookup", "soc-lookup").
        code_label: Label for error messages (e.g. "SIC", "SOC").

    Returns:
        The lookup result dict.

    Raises:
        HTTPException: 400 if description is empty, 404 if no result.
    """
    start_time = time.perf_counter()
    request_timestamp = int(time.time())
    lookup_id = f"{truncate_identifier(description)}_{request_timestamp}"
    logger.info(
        f"Request received for {endpoint_name}",
        description=truncate_identifier(description),
        similarity=str(similarity),
        lookup_id=lookup_id,
    )

    if not description:
        logger.error(
            f"Empty description provided in {code_label} lookup request",
            lookup_id=lookup_id,
        )
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    result = lookup_client.get_result(description, similarity)

    missing_exact_code = (
        not similarity
        and isinstance(result, dict)
        and not result.get("code")
    )
    if not result or missing_exact_code:
        logger.error(
            f"No {code_label} code found for description: {description}",
            lookup_id=lookup_id,
        )
        raise HTTPException(
            status_code=404,
            detail=f"No {code_label} code found for description: {description}",
        )

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    code = result.get("code") if isinstance(result, dict) else None
    logger.info(
        f"Response sent for {endpoint_name}",
        found=str(bool(code)),
        code=str(code or ""),
        similarity=str(similarity),
        duration_ms=str(duration_ms),
        lookup_id=lookup_id,
    )
    return result
