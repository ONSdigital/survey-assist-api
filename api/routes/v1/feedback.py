"""Feedback endpoint backed by Firestore."""

import time

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.feedback import (
    FeedbackResult,
    FeedbackResultResponse,
    FeedbackWithId,
    ListFeedbacksResponse,
)
from api.services.feedback_service import get_feedback, list_feedbacks, store_feedback

router = APIRouter(tags=["Feedback"])

logger = get_logger(__name__)


@router.post("/feedback", response_model=FeedbackResultResponse)
def store_feedback_endpoint(feedback_request: FeedbackResult) -> FeedbackResultResponse:
    """Store feedback data.

    Args:
        feedback_request (FeedbackResult): The feedback request containing case_id, person_id,
            survey_id, wave_id and questions data.

    Returns:
        FeedbackResultResponse: A response containing a success message and optional feedback_id.

    Raises:
        HTTPException: If there is an error processing the feedback.
    """
    try:
        start_time = time.perf_counter()
        feedback_body_id = (
            f"{feedback_request.case_id}:"
            f"{feedback_request.person_id}:"
            f"{feedback_request.wave_id}"
        )
        logger.info(
            "Request received for feedback",
            case_id=str(feedback_request.case_id),
            person_id=str(feedback_request.person_id),
            survey_id=str(feedback_request.survey_id),
            wave_id=str(feedback_request.wave_id),
            questions_count=str(len(feedback_request.questions)),
            feedback_body_id=feedback_body_id,
        )

        document_id = store_feedback(feedback_request.model_dump())
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for feedback",
            feedback_id=str(document_id),
            feedback_body_id=feedback_body_id,
            duration_ms=str(duration_ms),
        )
        return FeedbackResultResponse(
            message="Feedback received successfully", feedback_id=document_id
        )
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/feedback", response_model=FeedbackResult)
async def get_feedback_endpoint(feedback_id: str) -> FeedbackResult:
    """Retrieve a feedback result from Firestore by document ID.

    Args:
        feedback_id (str): The unique identifier of the feedback to retrieve.

    Returns:
        FeedbackResult: The retrieved feedback result.

    Raises:
        HTTPException: If the feedback is not found or there is an error retrieving it.
    """
    try:
        start_time = time.perf_counter()
        feedback_body_id = feedback_id
        logger.info(
            "Request received for feedback get",
            feedback_id=str(feedback_id),
            feedback_body_id=feedback_body_id,
        )
        feedback_data = get_feedback(feedback_id, correlation_id=feedback_body_id)
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for feedback get",
            feedback_id=str(feedback_id),
            feedback_body_id=feedback_body_id,
            duration_ms=str(duration_ms),
        )
        return FeedbackResult(**feedback_data)
    except FileNotFoundError as e:
        logger.warning(
            f"Feedback not found: {feedback_id}",
            feedback_body_id=feedback_body_id,
        )
        raise HTTPException(status_code=404, detail="Feedback not found") from e
    except ValueError as e:
        # pylint: disable=duplicate-code
        logger.error(
            f"Storage error retrieving feedback: {e}",
            feedback_body_id=feedback_body_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        # pylint: disable=duplicate-code
        logger.error(
            f"Storage service error retrieving feedback: {e}",
            feedback_body_id=feedback_body_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving feedback: {e}",
            feedback_body_id=feedback_body_id,
        )
        # pylint: disable=duplicate-code
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e


@router.get("/feedbacks", response_model=ListFeedbacksResponse)
async def list_feedbacks_endpoint(
    survey_id: str, wave_id: str, case_id: str | None = None
) -> ListFeedbacksResponse:
    """List feedback results filtered by survey_id, wave_id, and optionally case_id.

    Args:
        survey_id (str): Survey identifier to filter by.
        wave_id (str): Wave identifier to filter by.
        case_id (str | None): Optional case identifier to filter by.
            If None, returns all feedback for the survey/wave.

    Returns:
        ListFeedbacksResponse: List of matching feedback results with their document IDs.

    Raises:
        HTTPException: If there is an error retrieving the feedback results.
    """
    try:
        start_time = time.perf_counter()
        feedback_body_id = f"{survey_id}:{wave_id}:{case_id or ''}"
        logger.info(
            "Request received for feedbacks list",
            survey_id=str(survey_id),
            wave_id=str(wave_id),
            case_id=str(case_id),
            feedback_body_id=feedback_body_id,
        )
        feedbacks_data = list_feedbacks(
            survey_id, wave_id, case_id, correlation_id=feedback_body_id
        )
        feedbacks = [FeedbackWithId(**data) for data in feedbacks_data]
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for feedbacks list",
            count=str(len(feedbacks)),
            feedback_body_id=feedback_body_id,
            duration_ms=str(duration_ms),
        )
        return ListFeedbacksResponse(results=feedbacks, count=len(feedbacks))
    except ValueError as e:
        # pylint: disable=duplicate-code
        logger.error(
            f"Storage error retrieving feedbacks: {e}",
            feedback_body_id=feedback_body_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service unavailable: {e!s}"
        ) from e
    except RuntimeError as e:
        # pylint: disable=duplicate-code
        logger.error(
            f"Storage service error retrieving feedbacks: {e}",
            feedback_body_id=feedback_body_id,
        )
        raise HTTPException(
            status_code=503, detail=f"Storage service error: {e!s}"
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving feedbacks: {e}",
            feedback_body_id=feedback_body_id,
        )
        # pylint: disable=duplicate-code
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e!s}"
        ) from e
