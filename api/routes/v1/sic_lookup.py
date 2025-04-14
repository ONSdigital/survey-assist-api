"""SIC Lookup Route.

This module provides the SIC lookup endpoint for the Survey Assist API.
It handles requests to look up SIC codes based on business descriptions.
"""

from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Query

from api.services.sic_lookup_client import SICLookupClient

router = APIRouter()

# Initialize the SIC lookup client
lookup_client = SICLookupClient()


@router.get("/sic-lookup")
def sic_lookup(
    description: str = Query(..., description="Business description to look up"),
    similarity: bool = Query(False, description="Whether to use similarity search"),
) -> dict:
    """Look up a SIC code based on a business description.

    Args:
        description (str): The business description to look up.
        similarity (bool, optional): Whether to use similarity search.
            Defaults to False.

    Returns:
        dict: A dictionary containing the SIC code and description, or
            potential matches if similarity search is enabled.

    Raises:
        HTTPException: If the SIC lookup service is not initialized or if
            an error occurs during the lookup.
    """
    try:
        return lookup_client.lookup_sic_code(description, similarity)
    except RuntimeError as e:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="SIC lookup service is not available",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error looking up SIC code: {str(e)}",
        ) from e


@router.get("/test")
async def test():
    """Test endpoint to verify the API is working.

    Returns:
        dict: A message indicating the test endpoint is working.
    """
    return {"message": "Test endpoint is working"}
