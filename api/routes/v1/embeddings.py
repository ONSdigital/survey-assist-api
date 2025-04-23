"""Module that provides the embeddings endpoint for the Survey Assist API.

This module contains the embeddings endpoint for the Survey Assist API.
It defines the endpoint for checking the status of the embeddings in the vector store.
"""

from fastapi import APIRouter, Depends

from api.services.vector_store_client import VectorStoreClient

router = APIRouter(tags=["Embeddings"])


def get_vector_store_client() -> VectorStoreClient:
    """Get a vector store client instance.

    Returns:
        VectorStoreClient: A vector store client instance.
    """
    return VectorStoreClient()


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
    return await vector_store_client.get_status()
