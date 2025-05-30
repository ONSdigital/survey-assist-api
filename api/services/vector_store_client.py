"""Module that provides the vector store client for the Survey Assist API.

This module contains the vector store client for the Survey Assist API.
It defines the client for interacting with the SIC Vector Store service.
"""

import logging
from typing import Any, Dict, List

import httpx
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class VectorStoreClient:
    """Client for interacting with the SIC Vector Store service.

    This client provides methods for searching the vector store and getting its status.
    """

    def __init__(self, base_url: str = "http://localhost:8088"):
        """Initialize the vector store client.

        Args:
            base_url (str, optional): Base URL for the vector store service. Defaults to "http://localhost:8088".
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=base_url)

    async def search(
        self, industry_descr: str | None, job_title: str, job_description: str
    ) -> List[Dict[str, Any]]:
        """Search the vector store for similar SIC codes.

        Args:
            industry_descr (str | None): Industry description.
            job_title (str): Job title.
            job_description (str): Job description.

        Returns:
            List[Dict[str, Any]]: List of search results.

        Raises:
            RuntimeError: If the search fails.
        """
        try:
            response = await self.client.post(
                "/v1/sic-vector-store/search-index",
                json={
                    "industry_descr": industry_descr,
                    "job_title": job_title,
                    "job_description": job_description,
                },
            )
            response.raise_for_status()
            return response.json()["results"]
        except httpx.HTTPError as e:
            logger.error("Error searching vector store: %s", e)
            raise RuntimeError(f"Error searching vector store: {e}") from e

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the vector store service.

        Returns:
            Dict[str, Any]: Status information.

        Raises:
            RuntimeError: If getting the status fails.
        """
        try:
            response = await self.client.get("/v1/sic-vector-store/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Error getting vector store status: %s", e)
            raise RuntimeError(f"Error getting vector store status: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose() 