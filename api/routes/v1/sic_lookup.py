"""Module that provides the SIC lookup endpoint for the Survey Assist API.

This module contains the SIC lookup endpoint for the Survey Assist API.
It defines the endpoint for looking up SIC codes based on descriptions.
"""

# pylint: disable=duplicate-code  # SIC/SOC routes share structure by design

from typing import Any

from fastapi import APIRouter, Depends, Request
from survey_assist_utils.logging import get_logger

from api.routes.v1.lookup_handlers import execute_lookup_request
from api.services.sic_lookup_client import SICLookupClient
from api.services.sic_vector_store_client import SICVectorStoreClient

logger = get_logger(__name__)

router = APIRouter(tags=["SIC Lookup"])


def get_lookup_client(request: Request) -> SICLookupClient:
    """Get a SIC lookup client instance.

    Args:
        request: The FastAPI request object containing the app state.

    Returns:
        SICLookupClient: A SIC lookup client instance.
    """
    return request.app.state.sic_lookup_client


lookup_client_dependency = Depends(get_lookup_client)


def get_sic_vector_store_client(request: Request) -> SICVectorStoreClient:
    """Get the application-scoped SIC vector-store client."""
    return request.app.state.sic_vector_store_client


sic_vector_store_dependency = Depends(get_sic_vector_store_client)


@router.get("/sic-lookup")
async def sic_lookup(
    description: str,
    similarity: bool = False,
    lookup_client: SICLookupClient = lookup_client_dependency,
    vector_store_client: SICVectorStoreClient = sic_vector_store_dependency,
):
    """Lookup the SIC code for a given description.

    Args:
        description (str): The description to look up.
        similarity (bool, optional): Whether to use similarity search. Defaults to False.
        lookup_client (SICLookupClient): The SIC lookup client instance.
        vector_store_client (SICVectorStoreClient): The SIC vector store client instance.

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
    if similarity is False:
        logger.info("SIC similarity search - using vector store")
        return execute_lookup_request(
            description=description,
            similarity=similarity,
            lookup_client=lookup_client,
            endpoint_name="sic-lookup",
            code_label="SIC",
        )

    else:
        logger.info("SAYT test code executed - using vector store")
        results: list[dict[str, Any]] = await vector_store_client.search(
            industry_descr=description,
            job_title=description,
            job_description=description,
        )

        logger.info(
            "SIC SAYT results",
            description=description,
            results=results,
        )

        ordered_results = sorted(
            results,
            key=lambda result: float(result["distance"]),
        )

        # seen: set[tuple[str, str]] = set() #for unique_key = (code, title)
        seen: set[str] = set()  # for unique_key = code
        unique_results: list[dict[str, str]] = []

        for result in ordered_results:
            code = str(result["code"])
            title = str(result["title"])
            unique_key = code

            if unique_key in seen:
                continue

            seen.add(unique_key)
            unique_results.append(
                {
                    "en": f"{code} - {title}",
                }
            )

        return unique_results
