"""Module that provides the SIC lookup endpoint for the Survey Assist API.

This module contains the SIC lookup endpoint for the Survey Assist API.
It defines the endpoint for looking up SIC codes based on descriptions.
"""

import os

from fastapi import APIRouter, Depends, HTTPException
from survey_assist_utils.logging import get_logger

from api.services.sic_lookup_client import SICLookupClient

router = APIRouter(tags=["SIC Lookup"])
logger = get_logger(__name__)


def get_lookup_client() -> SICLookupClient:
    """Get a SIC lookup client instance.

    Returns:
        SICLookupClient: A SIC lookup client instance.
    """
    data_path = os.getenv("SIC_LOOKUP_DATA_PATH")
    if data_path and data_path.strip():
        logger.info(f"Using SIC lookup data from environment: {data_path}")
        return SICLookupClient(data_path=data_path.strip())  # Pass the path!

    logger.info("SIC_LOOKUP_DATA_PATH not set, using package example data")
    return SICLookupClient()  # No path = uses package data


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

    return result
