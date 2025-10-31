"""Feedback endpoint backed by Firestore."""

import time

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.feedback import FeedbackResult, FeedbackResultResponse
from api.services.feedback_service import store_feedback

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
