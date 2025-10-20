"""Feedback endpoint backed by Firestore."""

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.feedback import FeedbackResult, FeedbackResultResponse
from api.services.firestore_client import get_firestore_client

router = APIRouter(tags=["Feedback"])

logger = get_logger(__name__)


@router.post("/feedback", response_model=FeedbackResultResponse)
async def store_feedback(feedback_request: FeedbackResult) -> FeedbackResultResponse:
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
        logger.info(f"Received feedback for case_id: {feedback_request.case_id}")
        logger.info(f"Person ID: {feedback_request.person_id}")
        logger.info(f"Survey ID: {feedback_request.survey_id}")
        logger.info(f"Wave ID: {feedback_request.wave_id}")
        logger.info(f"Number of questions: {len(feedback_request.questions)}")

        # Log feedback details for debugging
        for question in feedback_request.questions:
            logger.info(f"Question response_name: {question.response_name}")
            logger.info(f"Response: {question.response[:50]}...")
            if question.response_options:
                logger.info(f"Response options: {question.response_options}")

        db = get_firestore_client()
        doc_ref = db.collection("survey_feedback").document()
        doc_ref.set(feedback_request.model_dump())
        logger.info(f"Stored feedback in Firestore with id {doc_ref.id}")
        return FeedbackResultResponse(
            message="Feedback received successfully", feedback_id=doc_ref.id
        )
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
