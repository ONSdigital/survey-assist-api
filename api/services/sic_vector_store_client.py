"""Vector store client service for the Survey Assist API.

This module provides a client for the vector store service, which is used to
check the status of the embeddings.
"""

import logging
from http import HTTPStatus

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class SICVectorStoreClient:  # pylint: disable=too-few-public-methods
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

    async def get_status(self) -> dict[str, str]:
        """Get the status of the vector store.

        Returns:
            Dict containing the status of the vector store.

        Raises:
            HTTPException: If the request to the vector store fails.
        """
        try:
            url = f"{self.base_url}/v1/sic-vector-store/status"
            logger.info("Attempting to connect to vector store at: %s", url)
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                logger.info("Vector store response status: %s", response.status_code)
                response.raise_for_status()
                result = response.json()
                logger.info("Vector store response: %s", result)
                return result
        except httpx.HTTPError as e:
            logger.error("Failed to connect to vector store: %s", str(e))
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to vector store: {e!s}",
            ) from e
        except Exception as e:
            logger.error("Unexpected error connecting to vector store: %s", str(e))
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error connecting to vector store: {e!s}",
            ) from e
