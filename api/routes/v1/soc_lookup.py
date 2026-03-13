"""Module that provides the SOC lookup endpoint for the Survey Assist API.

This module contains the SOC lookup endpoint for the Survey Assist API.
It defines the endpoint for looking up SOC codes based on descriptions.
"""

# pylint: disable=duplicate-code  # SIC/SOC routes share structure by design

from fastapi import APIRouter, Depends, Request

from api.routes.v1.lookup_handlers import execute_lookup_request
from api.services.soc_lookup_client import SOCLookupClient

router = APIRouter(tags=["SOC Lookup"])


def get_lookup_client(request: Request) -> SOCLookupClient:
    """Get a SOC lookup client instance.

    Args:
        request: The FastAPI request object containing the app state.

    Returns:
        SOCLookupClient: A SOC lookup client instance.
    """
    return request.app.state.soc_lookup_client


lookup_client_dependency = Depends(get_lookup_client)


@router.get("/soc-lookup")
async def soc_lookup(
    description: str,
    similarity: bool = False,
    lookup_client: SOCLookupClient = lookup_client_dependency,
):
    """Lookup the SOC code for a given description.

    Args:
        description: The description to look up.
        similarity: Whether to use similarity search. Defaults to False.
        lookup_client: The SOC lookup client instance.

    Returns:
        dict: The SOC lookup result.
    """
    return execute_lookup_request(
        description=description,
        similarity=similarity,
        lookup_client=lookup_client,
        endpoint_name="soc-lookup",
        code_label="SOC",
    )
