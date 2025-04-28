"""Module that provides the embeddings endpoint for the Survey Assist API.

This module contains the embeddings endpoint for the Survey Assist API.
It defines the endpoint for checking the status of the embeddings in the vector store.
"""

import os

from fastapi import APIRouter, Depends

from api.services.vector_store_client import VectorStoreClient

router = APIRouter(tags=["Embeddings"])


def get_vector_store_client() -> VectorStoreClient:
    """Get a vector store client instance.

    Returns:
        VectorStoreClient: A vector store client instance.
    """
    # Default to local development URL
    base_url = "http://0.0.0.0:8088"

    # Only use environment variable if it's set and not empty
    env_url = os.getenv("SIC_VECTOR_STORE")
    if env_url and env_url.strip():
        base_url = env_url.strip()

    return VectorStoreClient(base_url=base_url)


# Define the dependency at module level
vector_store_client_dependency = Depends(get_vector_store_client)


@router.get("/embeddings")
async def get_embeddings_status(
    vector_store_client: VectorStoreClient = vector_store_client_dependency,
) -> dict:
    """Get the status of the embeddings in the vector store.

    Args:
        vector_store_client: The vector store client instance.

    Returns:
        dict: A dictionary containing the status of the embeddings.

    Example:
        ```json
        {
            "status": "ready",
            "message": "Embeddings are loaded and ready to query"
        }
        ```
    """
    status = await vector_store_client.get_status()
    return status
