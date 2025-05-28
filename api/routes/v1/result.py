"""Module that provides the result endpoint for the Survey Assist API.

This module contains the result endpoint for the Survey Assist API.
It defines the endpoint for storing classification results.
"""

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.result import ResultRequest, ResultResponse

router: APIRouter = APIRouter(tags=["Results"])
logger = get_logger(__name__)


@router.post("/result", response_model=ResultResponse)
async def store_result(request: ResultRequest) -> ResultResponse:
    """Store a classification result.

    Args:
        request (ResultRequest): The request containing the result data to store.

    Returns:
        ResultResponse: A response containing the user ID and survey name.

    Raises:
        HTTPException: If the input is invalid or processing fails.
    """
    # Validate input
    if not request.user_id.strip() or not request.survey.strip():
        logger.error("Empty user_id or survey provided in result request")
        raise HTTPException(
            status_code=400, detail="User ID and survey name cannot be empty"
        )

    try:
        logger.info(
            f"Storing result for user {request.user_id}, survey {request.survey}"
        )

        # Mock result storage - in a real implementation, this would store the result
        # in a database or other persistent storage
        return ResultResponse(user_id=request.user_id, survey=request.survey)

    except Exception as e:
        logger.error(f"Failed to store result: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Failed to store result: {e!s}"
        ) from e
