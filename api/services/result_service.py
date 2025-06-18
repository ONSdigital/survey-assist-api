"""Module that provides the result service for the Survey Assist API.

This module contains the result service that handles storing and retrieving
classification results in GCP. It provides functionality to store results
in a GCP bucket and retrieve them using a unique identifier.
"""

import json
from datetime import datetime
from typing import Any

from google.cloud import storage
from survey_assist_utils.logging import get_logger

from api.config import settings

logger = get_logger(__name__)


def datetime_handler(obj):
    """Handle datetime serialisation for JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def store_result(result_data: dict[str, Any], filename: str) -> None:
    """Store a result in GCP.

    Args:
        result_data (dict[str, Any]): The result data to store.
        filename (str): The filename to store the result under.

    Raises:
        Exception: If there is an error storing the result.
    """
    try:
        # Initialise GCP client
        client = storage.Client()
        bucket = client.bucket(settings.GCP_BUCKET_NAME)

        # Create a new blob and upload the result data
        blob = bucket.blob(filename)
        blob.upload_from_string(
            json.dumps(result_data, indent=2, default=datetime_handler),
            content_type="application/json",
        )

        logger.info(f"Successfully stored result in {filename}")
    except Exception as e:
        logger.error(f"Error storing result: {e!s}")
        # Raising a general exception here because storage errors can be varied and unpredictable.
        raise RuntimeError(f"Failed to store result: {e!s}") from e


def get_result(result_id: str) -> dict[str, Any]:
    """Retrieve a result from GCP.

    Args:
        result_id (str): The unique identifier of the result to retrieve.

    Returns:
        dict[str, Any]: The retrieved result data.

    Raises:
        Exception: If the result is not found or there is an error retrieving it.
    """
    try:
        # Initialise GCP client
        client = storage.Client()
        bucket = client.bucket(settings.GCP_BUCKET_NAME)

        # Get the blob and download the result data
        blob = bucket.blob(result_id)
        if not blob.exists():
            raise FileNotFoundError(f"Result not found: {result_id}")

        result_data = json.loads(blob.download_as_string())

        logger.info(f"Successfully retrieved result from {result_id}")
        return result_data
    except Exception as e:
        logger.error(f"Error retrieving result: {e!s}")
        # Raising a general exception here because retrieval errors can be varied and unpredictable.
        raise RuntimeError(f"Failed to retrieve result: {e!s}") from e
