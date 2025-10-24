"""Result service for storing and retrieving results in Firestore."""

from datetime import datetime
from typing import Any

from google.api_core.retry import Retry
from google.api_core.exceptions import ServiceUnavailable
from survey_assist_utils.logging import get_logger

from api.services.firestore_client import get_firestore_client

logger = get_logger(__name__)

# Configure retry for Firestore operations
retry_config = Retry(
    predicate=lambda exc: isinstance(exc, ServiceUnavailable),
    initial=0.5,
    maximum=10.0,
    multiplier=1.5,
    deadline=30.0,
    on_error=lambda exc: logger.warning(f"Retrying due to: {exc}")
)


def datetime_handler(obj):
    """Handle datetime serialisation for JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def store_result(result_data: dict[str, Any]) -> str:
    """Store a result document in Firestore `survey_results` and return its ID.

    Args:
        result_data (dict[str, Any]): The result data to store.

    Returns:
        str: Firestore document ID.
    """
    db = get_firestore_client()
    doc_ref = db.collection("survey_results").document()
    doc_ref.set(result_data)
    logger.info(f"Stored result in Firestore with id {doc_ref.id}")
    return doc_ref.id


def get_result(result_id: str) -> dict[str, Any]:
    """Retrieve a result document from Firestore by ID.

    Args:
        result_id (str): Firestore document ID.

    Returns:
        dict[str, Any]: The retrieved document data.
    """
    db = get_firestore_client()
    doc = db.collection("survey_results").document(result_id).get(retry=retry_config)
    if not doc.exists:
        raise FileNotFoundError(f"Result not found: {result_id}")
    data = doc.to_dict()
    logger.info(f"Retrieved result id {result_id} from Firestore")
    return data


def list_results(survey_id: str, wave_id: str, case_id: str) -> list[dict[str, Any]]:
    """List result documents from Firestore filtered by survey_id, wave_id, and case_id.

    Args:
        survey_id (str): Survey identifier to filter by.
        wave_id (str): Wave identifier to filter by.
        case_id (str): Case identifier to filter by.

    Returns:
        list[dict[str, Any]]: List of matching result documents with their IDs.
    """
    db = get_firestore_client()
    collection = db.collection("survey_results")

    # Query documents where survey_id, wave_id, and case_id match
    query = (
        collection.where("survey_id", "==", survey_id)
        .where("wave_id", "==", wave_id)
        .where("case_id", "==", case_id)
    )

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        data["document_id"] = doc.id  # Include the Firestore document ID
        results.append(data)

    logger.info(
        f"Retrieved {len(results)} results for survey_id={survey_id}, "
        f"wave_id={wave_id}, case_id={case_id}"
    )
    return results
