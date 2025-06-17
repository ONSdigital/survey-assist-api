"""Module that provides the result service for the Survey Assist API.

This module contains the result service that handles storing and retrieving
classification results in GCP. It provides functionality to store results
in a GCP bucket and retrieve them using a unique identifier.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from api.config import settings

logger = logging.getLogger(__name__)


def datetime_handler(obj):
    """Handle datetime serialization for JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def store_result(result_data: Dict[str, Any], filename: str) -> None:
    """Store a result in GCP.

    Args:
        result_data (Dict[str, Any]): The result data to store.
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
            content_type='application/json'
        )
        
        logger.info(f"Successfully stored result in {filename}")
    except Exception as e:
        logger.error(f"Error storing result: {str(e)}")
        raise Exception(f"Failed to store result: {str(e)}")


def get_result(result_id: str) -> Dict[str, Any]:
    """Retrieve a result from GCP.

    Args:
        result_id (str): The unique identifier of the result to retrieve.

    Returns:
        Dict[str, Any]: The retrieved result data.

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
            raise Exception(f"Result not found: {result_id}")
            
        result_data = json.loads(blob.download_as_string())
        
        logger.info(f"Successfully retrieved result from {result_id}")
        return result_data
    except Exception as e:
        logger.error(f"Error retrieving result: {str(e)}")
        raise Exception(f"Failed to retrieve result: {str(e)}") 