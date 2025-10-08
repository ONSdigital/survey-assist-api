"""Module that provides the feedback endpoint for the Survey Assist API.

This module contains the feedback endpoint that allows storing feedback data.
It provides functionality to receive and process feedback requests.
"""

from fastapi import APIRouter, HTTPException
from survey_assist_utils.logging import get_logger

from api.models.feedback import FeedbackRequest, FeedbackResponseModel

router = APIRouter(tags=["Feedback"])

logger = get_logger(__name__)


@router.post("/feedback", response_model=FeedbackResponseModel)
async def store_feedback(feedback_request: FeedbackRequest) -> FeedbackResponseModel:
    """Store feedback data.

    Args:
        feedback_request (FeedbackRequest): The feedback request containing case_id and
            feedback data.

    Returns:
        FeedbackResponseModel: A response containing a success message.

    Raises:
        HTTPException: If there is an error processing the feedback.
    """
    try:
        logger.info(f"Received feedback for case_id: {feedback_request.case_id}")
        logger.info(f"Number of feedback entries: {len(feedback_request.feedback)}")

        # Log feedback details for debugging
        for person_feedback in feedback_request.feedback:
            logger.info(
                f"Person ID: {person_feedback.person_id}, "
                f"Responses: {len(person_feedback.response)}"
            )
            for response in person_feedback.response:
                logger.info(f"Question: {response.question[:50]}...")
                logger.info(f"Answer: {response.answer[:50]}...")
                if response.options:
                    logger.info(f"Options: {response.options}")

        return FeedbackResponseModel(message="Feedback received successfully")
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
