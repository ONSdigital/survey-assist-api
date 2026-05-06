"""Module that provides the embeddings endpoint for the Survey Assist API.

This module contains the embeddings endpoint for the Survey Assist API.
It defines the endpoint for checking the status of the embeddings in the vector store.
"""

import os
import time
from typing import Annotated

from fastapi import APIRouter, Depends
from survey_assist_utils.logging import get_logger

from api.models.embeddings import EMBEDDINGS_STATUS_EXAMPLE, StatusResponse
from api.services.sic_vector_store_client import SICVectorStoreClient

router = APIRouter(tags=["Embeddings"])
logger = get_logger(__name__)


def get_vector_store_client() -> SICVectorStoreClient:
    """Get a vector store client instance.

    Returns:
        SICVectorStoreClient: A vector store client instance.
    """
    # Default to local development URL
    base_url = "http://localhost:8088"

    # Only use environment variable if it's set and not empty
    env_url = os.getenv("SIC_VECTOR_STORE")
    if env_url and env_url.strip():
        base_url = env_url.strip()
        logger.debug(f"Using vector store URL from environment: {base_url}")
    else:
        logger.debug("Using default vector store URL: http://localhost:8088")

    return SICVectorStoreClient(base_url=base_url)


@router.get(
    "/embeddings",
    response_model=StatusResponse,
    responses={
        200: {
            "description": "Current SIC vector store status",
            "content": {"application/json": {"example": EMBEDDINGS_STATUS_EXAMPLE}},
        }
    },
)
async def get_embeddings_status(
    vector_store_client: Annotated[
        SICVectorStoreClient, Depends(get_vector_store_client)
    ],
) -> StatusResponse:
    """Get the status of the embeddings in the vector store.

    Args:
        vector_store_client: The vector store client instance.

    Returns:
        StatusResponse: The status of the embeddings.
    """
    start_time = time.perf_counter()
    logger.info("Request received for embeddings status")
    status = await vector_store_client.get_status()
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        "Response sent for embeddings status",
        status_value=(
            str(status.get("status")) if isinstance(status, dict) else "unknown"
        ),
        duration_ms=str(duration_ms),
    )
    return StatusResponse.model_validate(status)
