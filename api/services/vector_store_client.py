"""Vector store client service for the Survey Assist API.

This module provides a client for the vector store service, which is used to
check the status of the embeddings.
"""

from fastapi import HTTPException
import httpx


class VectorStoreClient:
    """Client for the vector store service.

    This class provides a client for the vector store service, which is used to
    check the status of the embeddings.

    Attributes:
        base_url: The base URL of the vector store service.
    """

    def __init__(self, base_url: str = "http://0.0.0.0:8088") -> None:
        """Initialize the vector store client.

        Args:
            base_url: The base URL of the vector store service.
        """
        self.base_url = base_url

    async def get_status(self) -> dict:
        """Get the status of the vector store.

        Returns:
            dict: A dictionary containing the status of the vector store.

        Raises:
            HTTPException: If the request to the vector store fails.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/status")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to vector store: {str(e)}",
            ) 