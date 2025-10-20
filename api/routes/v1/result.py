"""Result endpoints backed by Firestore."""

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
    """Store a survey result in Firestore and return its document ID."""
    try:
        doc_id = store_result(result.model_dump())
        return ResultResponse(message="Result stored successfully", result_id=doc_id)
    except ValueError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        logger.error(f"Storage service error: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error storing result: {e}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


@router.get("/result", response_model=SurveyAssistResult)
async def get_survey_result(result_id: str) -> SurveyAssistResult:
    """Retrieve a survey result from Firestore by document ID.

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
        logger.error(f"Storage error retrieving result: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        logger.error(f"Storage service error retrieving result: {e}")
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error retrieving result: {e}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e
