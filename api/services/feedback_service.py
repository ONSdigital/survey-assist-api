"""Feedback service for storing and retrieving feedback in Firestore.

Note: While currently only storing feedback is implemented, retrieval functionality
will be needed in the future for analytics and reporting purposes.
"""

from typing import Any

from survey_assist_utils.logging import get_logger

from api.services.firestore_client import get_firestore_client

logger = get_logger(__name__)


def store_feedback(feedback_data: dict[str, Any]) -> str:
    """Store feedback document in Firestore `survey_feedback` collection and return its ID.

    Args:
        feedback_data (dict[str, Any]): The feedback data to store.

    Returns:
        str: Firestore document ID.
    """
    db = get_firestore_client()
    doc_ref = db.collection("survey_feedback").document()
    doc_ref.set(feedback_data)
    logger.info(f"Stored feedback in Firestore with id {doc_ref.id}")
    return doc_ref.id


# Future development will include retrieval functions for analytics and reporting:
# - get_feedback(feedback_id: str) -> dict[str, Any]
# - list_feedback(survey_id: str, wave_id: str, case_id: str) -> list[dict[str, Any]]
# - get_feedback_by_person(person_id: str) -> list[dict[str, Any]]
