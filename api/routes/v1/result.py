"""Result endpoints backed by Firestore."""

import time

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.result import (
    ListResultsResponse,
    ResultResponse,
    ResultWithId,
    SurveyAssistResult,
)
from api.services.result_service import get_result, list_results, store_result

router = APIRouter(tags=["Result"])

logger = get_logger(__name__)


@router.post("/result", response_model=ResultResponse)
async def store_survey_result(result: SurveyAssistResult) -> ResultResponse:
    """Store a survey result in Firestore and return its document ID."""
    try:
        start_time = time.perf_counter()
        result_id = f"{result.survey_id}:{result.wave_id}:{result.case_id}"
        logger.info(
            "Request received for result store",
            survey_id=str(result.survey_id),
            wave_id=str(result.wave_id),
            case_id=str(result.case_id),
            result_id=result_id,
        )
        doc_id = store_result(result.model_dump())
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for result store",
            result_id=str(doc_id),
            correlation_result_id=result_id,
            duration_ms=str(duration_ms),
        )
        return ResultResponse(message="Result stored successfully", result_id=doc_id)
    except ValueError as e:
        logger.error(f"Storage error: {e}", correlation_result_id=result_id)
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        logger.error(f"Storage service error: {e}", correlation_result_id=result_id)
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error storing result: {e}", correlation_result_id=result_id
        )
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
        start_time = time.perf_counter()
        correlation_result_id = result_id
        logger.info(
            "Request received for result get",
            result_id=str(result_id),
            correlation_result_id=correlation_result_id,
        )
        result_data = get_result(result_id)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for result get",
            result_id=str(result_id),
            correlation_result_id=correlation_result_id,
            duration_ms=str(duration_ms),
        )
        return SurveyAssistResult(**result_data)
    except FileNotFoundError as e:
        logger.warning(
            f"Result not found: {result_id}",
            correlation_result_id=correlation_result_id,
        )
        raise HTTPException(status_code=404, detail="Result not found") from e
    except ValueError as e:
        logger.error(
            f"Storage error retrieving result: {e}",
            correlation_result_id=correlation_result_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        logger.error(
            f"Storage service error retrieving result: {e}",
            correlation_result_id=correlation_result_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving result: {e}",
            correlation_result_id=correlation_result_id,
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


@router.get("/results", response_model=ListResultsResponse)
async def list_survey_results(
    survey_id: str, wave_id: str, case_id: str | None = None
) -> ListResultsResponse:
    """List survey results filtered by survey_id, wave_id, and optionally case_id.

    Args:
        survey_id (str): Survey identifier to filter by.
        wave_id (str): Wave identifier to filter by.
        case_id (str | None): Optional case identifier to filter by.
            If None, returns all results for the survey/wave.

    Returns:
        ListResultsResponse: List of matching survey results with their document IDs.

    Raises:
        HTTPException: If there is an error retrieving the results.
    """
    try:
        start_time = time.perf_counter()
        result_id = f"{survey_id}:{wave_id}:{case_id or ''}"
        logger.info(
            "Request received for results list",
            survey_id=str(survey_id),
            wave_id=str(wave_id),
            case_id=str(case_id),
            result_id=result_id,
        )
        results_data = list_results(survey_id, wave_id, case_id)
        results = [ResultWithId(**data) for data in results_data]
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for results list",
            count=str(len(results)),
            correlation_result_id=result_id,
            duration_ms=str(duration_ms),
        )
        return ListResultsResponse(results=results, count=len(results))
    except ValueError as e:
        logger.error(
            f"Storage error retrieving results: {e}", correlation_result_id=result_id
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        logger.error(
            f"Storage service error retrieving results: {e}",
            correlation_result_id=result_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving results: {e}", correlation_result_id=result_id
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e
