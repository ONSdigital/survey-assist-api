"""Module that provides the SIC lookup endpoint for the Survey Assist API.

This module contains the SIC lookup endpoint for the Survey Assist API.
It defines the endpoint for looking up SIC codes based on descriptions.
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from survey_assist_utils.logging import get_logger

from api.services.sic_lookup_client import SICLookupClient
from api.utils.logging_utils import truncate_identifier

router = APIRouter(tags=["SIC Lookup"])
logger = get_logger(__name__)


def get_lookup_client(request: Request) -> SICLookupClient:
    """Get a SIC lookup client instance.

    Args:
        request: The FastAPI request object containing the app state.

    Returns:
        SICLookupClient: A SIC lookup client instance.
    """
    return request.app.state.sic_lookup_client


# Define the dependency at module level
lookup_client_dependency = Depends(get_lookup_client)


@router.get("/sic-lookup")
async def sic_lookup(
    description: str,
    similarity: bool = False,
    lookup_client: SICLookupClient = lookup_client_dependency,
):
    """Lookup the SIC code for a given description.

    Args:
        description (str): The description to look up.
        similarity (bool, optional): Whether to use similarity search. Defaults to False.
        lookup_client (SICLookupClient): The SIC lookup client instance.

    Returns:
        dict: The SIC lookup result.

    Example:
        ```json
        {
            "code": "43210",
            "description": "Electrical installation",
            "potential_matches": {
                "descriptions": [
                    "Electrical installation",
                    "Electrical contractor",
                    "Electrician"
                ]
            }
        }
    ```
    """
    start_time = time.perf_counter()
    logger.info(
        "Request received for sic-lookup",
        description=truncate_identifier(description),
        similarity=str(similarity),
    )

    if not description:
        logger.error("Empty description provided in SIC lookup request")
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    result = lookup_client.get_result(description, similarity)
    if not result:
        logger.error(f"No SIC code found for description: {description}")
        raise HTTPException(
            status_code=404,
            detail=f"No SIC code found for description: {description}",
        )

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        "Response sent for sic-lookup",
        found=str(bool(result)),
        similarity=str(similarity),
        duration_ms=str(duration_ms),
    )
    return result
