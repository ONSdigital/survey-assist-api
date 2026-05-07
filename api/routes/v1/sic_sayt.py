"""Module that provides the SIC search-as-you-type endpoint for the Survey Assist API."""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from survey_assist_utils.logging import get_logger

from api.models.sic_sayt import SIC_SAYT_RESPONSE_EXAMPLE, SICSaytResponse
from api.services.sic_sayt_client import SICSaytClient
from utils.survey import truncate_identifier

router = APIRouter(tags=["SIC SAYT"])
logger = get_logger(__name__)


def get_sayt_client(request: Request) -> SICSaytClient:
    """Get a SIC SAYT client instance from application state."""
    return request.app.state.sic_sayt_client


@router.get(
    "/sic-sayt",
    response_model=SICSaytResponse,
    responses={
        200: {
            "description": "SIC search-as-you-type suggestions",
            "content": {"application/json": {"example": SIC_SAYT_RESPONSE_EXAMPLE}},
        }
    },
)
async def sic_sayt(
    description: str,
    sayt_client: Annotated[SICSaytClient, Depends(get_sayt_client)],
    num_suggestions: Annotated[int | None, Query(ge=1, le=100)] = None,
) -> SICSaytResponse:
    """Return SIC description suggestions as the user types.

    Args:
        description: Partial SIC description entered by the user.
        num_suggestions: Optional maximum number of suggestions to return.
        sayt_client: The SIC SAYT client instance.

    Returns:
        SICSaytResponse: Matching suggestion strings.

    Raises:
        HTTPException: If an empty description is provided.
    """
    start_time = time.perf_counter()
    request_timestamp = int(time.time())
    request_id = f"{truncate_identifier(description)}_{request_timestamp}"
    logger.info(
        "Request received for sic-sayt",
        description=truncate_identifier(description),
        num_suggestions=str(num_suggestions or "default"),
        request_id=request_id,
    )

    if not description:
        logger.error(
            "Empty description provided in SIC SAYT request", request_id=request_id
        )
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    suggestions = sayt_client.get_suggestions(description, num_suggestions)

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        "Response sent for sic-sayt",
        suggestion_count=str(len(suggestions)),
        duration_ms=str(duration_ms),
        request_id=request_id,
    )
    return SICSaytResponse(suggestions=suggestions)
