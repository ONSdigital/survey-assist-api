"""Feedback service for storing and retrieving feedback in Firestore.

Note: While currently only storing feedback is implemented, retrieval functionality
will be needed in the future for analytics and reporting purposes.
"""

from typing import Any

from survey_assist_utils.logging import get_logger

from api.services.firestore_client import get_firestore_client, retry_config

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


def get_feedback(feedback_id: str, correlation_id: str | None = None) -> dict[str, Any]:
    """Retrieve a feedback document from Firestore by ID.

    Args:
        feedback_id (str): Firestore document ID.
        correlation_id (str | None): Optional correlation ID for request tracking.

    Returns:
        dict[str, Any]: The retrieved document data.

    Raises:
        FileNotFoundError: If the feedback document is not found.
    """
    db = get_firestore_client()
    doc = db.collection("survey_feedback").document(feedback_id).get(retry=retry_config)
    if not doc.exists:
        raise FileNotFoundError(f"Feedback not found: {feedback_id}")
    data = doc.to_dict()
    logger.info(
        f"Retrieved feedback id {feedback_id} from Firestore",
        correlation_id=correlation_id,
    )
    return data


def list_feedbacks(
    survey_id: str,
    wave_id: str,
    case_id: str | None = None,
    correlation_id: str | None = None,
) -> list[dict[str, Any]]:
    """List feedback documents from Firestore filtered by survey_id, wave_id, and case_id.

    Filters by survey_id, wave_id, and optionally case_id.

    Args:
        survey_id (str): Survey identifier to filter by.
        wave_id (str): Wave identifier to filter by.
        case_id (str | None): Optional case identifier to filter by.
            If None, returns all feedback for the survey/wave.
        correlation_id (str | None): Optional correlation ID for request tracking.

    Returns:
        list[dict[str, Any]]: List of matching feedback documents with their IDs.
    """
    db = get_firestore_client()
    collection = db.collection("survey_feedback")

    # Query documents where survey_id and wave_id match, optionally case_id
    # pylint: disable=duplicate-code
    query = collection.where("survey_id", "==", survey_id).where(
        "wave_id", "==", wave_id
    )

    # Add case_id filter if provided
    if case_id is not None:
        query = query.where("case_id", "==", case_id)

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["document_id"] = doc.id  # Include the Firestore document ID
        results.append(data)

    logger.info(
        f"Retrieved {len(results)} feedback results for survey_id={survey_id}, "
        f"wave_id={wave_id}, case_id={case_id}",
        correlation_id=correlation_id,
    )
    return results
