"""Module that provides the SIC lookup endpoint for the Survey Assist API.

This module contains the SIC lookup endpoint for the Survey Assist API.
It defines the endpoint for looking up SIC codes based on descriptions.
"""

import sys

from fastapi import APIRouter, HTTPException

from api.services.sic_lookup_client import SICLookupClient

router = APIRouter(tags=["SIC Lookup"])


def get_lookup_client() -> SICLookupClient:
    """Get a SIC lookup client instance.

    Returns:
        SICLookupClient: A SIC lookup client instance.
    """
    # Use test data during tests, knowledge base in production
    if "pytest" in sys.modules:
        return SICLookupClient(data_path="tests/data/example_sic_lookup_data.csv")
    return SICLookupClient()


# Initialize the SIC Lookup Client
lookup_client = get_lookup_client()


@router.get("/sic-lookup")
async def sic_lookup(description: str, similarity: bool = False):
    """Lookup the SIC code for a given description.

    Args:
        description (str): The description to look up.
        similarity (bool, optional): Whether to use similarity search. Defaults to False.

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
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    result = lookup_client.get_result(description, similarity)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No SIC code found for description: {description}",
        )

    return result


@router.get("/test")
async def test():
    """Test endpoint for the SIC lookup service.

    Returns:
        dict: A test response.
    """
    return {"message": "SIC lookup service is running"}
