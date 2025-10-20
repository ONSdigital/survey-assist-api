"""Result service for storing and retrieving results in Firestore."""

from datetime import datetime
from typing import Any

from survey_assist_utils.logging import get_logger

from api.services.firestore_client import get_firestore_client

logger = get_logger(__name__)


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
    doc = db.collection("survey_results").document(result_id).get()
    if not doc.exists:
        raise FileNotFoundError(f"Result not found: {result_id}")
    data = doc.to_dict()
    logger.info(f"Retrieved result id {result_id} from Firestore")
    return data
