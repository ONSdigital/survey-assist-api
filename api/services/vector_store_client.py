"""Module that provides the vector store client for the Survey Assist API.

This module contains the vector store client for the Survey Assist API.
It defines the client for interacting with the vector store service.
"""

from typing import Any

import httpx
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class VectorStoreClient:
    """Client for interacting with the vector store service.

    This class provides methods for searching the vector store and getting its status.
    """

    def __init__(self, base_url: str = "http://localhost:8088"):
        """Initialise the vector store client.

        Args:
            base_url (str, optional): The base URL of the vector store service.
                Defaults to "http://localhost:8088".
        """
        self.base_url = base_url

    async def search(
        self, industry_descr: str | None, job_title: str, job_description: str
    ) -> list[dict[str, Any]]:
        """Search the vector store for similar SIC codes.

        Args:
            industry_descr (str | None): The industry description.
            job_title (str): The job title.
            job_description (str): The job description.

        Returns:
            list[dict[str, Any]]: A list of search results, each containing a code,
                title, and distance.

        Raises:
            RuntimeError: If there is an error searching the vector store.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/sic-vector-store/search-index",
                    json={
                        "industry_descr": industry_descr,
                        "job_title": job_title,
                        "job_description": job_description,
                    },
                )
                response.raise_for_status()
                return response.json()["results"]
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise RuntimeError(f"Error searching vector store: {e}") from e

    async def get_status(self) -> dict[str, Any]:
        """Get the status of the vector store service.

        Returns:
            dict[str, Any]: A dictionary containing the status information.

        Raises:
            RuntimeError: If there is an error getting the status.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/v1/status")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting vector store status: {e}")
            raise RuntimeError(f"Error getting vector store status: {e}") from e
