"""Module that provides the result endpoint for the Survey Assist API.

This module contains the result endpoint that allows storing and retrieving
classification results. It provides functionality to store results in GCP
and retrieve them using a unique identifier.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.result import (
    ResultResponse,
    SurveyAssistResult,
)
from api.services.result_service import get_result, store_result

router = APIRouter(tags=["Result"])

logger = get_logger(__name__)


@router.post("/result", response_model=ResultResponse)
async def store_survey_result(result: SurveyAssistResult) -> ResultResponse:
    """Store a survey result in GCP.

    Args:
        result (SurveyAssistResult): The survey result to store.

    Returns:
        ResultResponse: A response containing a success message and the result ID.

    Raises:
        HTTPException: If there is an error storing the result.
    """
    try:
        # Generate a filename based on survey_id, user, date, and timestamp
        date_str = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H_%M_%S")
        filename = f"{result.survey_id}/{result.user}/{date_str}/{time_str}.json"

        # Store the result in GCP
        store_result(result.model_dump(), filename)

        return ResultResponse(message="Result stored successfully", result_id=filename)
    except ValueError as e:
        # GCP bucket/permission errors
        logger.error(f"GCP storage error: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        # Other GCP API errors
        logger.error(f"GCP API error: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error storing result: {e}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


@router.get("/result", response_model=SurveyAssistResult)
async def get_survey_result(result_id: str) -> SurveyAssistResult:
    """Retrieve a survey result from GCP.

    Args:
        result_id (str): The unique identifier of the result to retrieve.

    Returns:
        SurveyAssistResult: The retrieved survey result.

    Raises:
        HTTPException: If the result is not found or there is an error retrieving it.
    """
    try:
        result_data = get_result(result_id)
        return SurveyAssistResult(**result_data)
    except FileNotFoundError as e:
        logger.warning(f"Result not found: {result_id}")
        raise HTTPException(status_code=404, detail="Result not found") from e
    except ValueError as e:
        # GCP bucket/permission errors
        logger.error(f"GCP storage error retrieving result: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        # Other GCP API errors
        logger.error(f"GCP API error retrieving result: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error retrieving result: {e}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e
