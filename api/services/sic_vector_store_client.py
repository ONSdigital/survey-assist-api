"""Vector store client service for the Survey Assist API.

This module provides a client for the vector store service, which is used to
check the status of the embeddings.
"""

from http import HTTPStatus
from typing import Any

import httpx
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class SICVectorStoreClient:  # pylint: disable=too-few-public-methods
    """Client for the vector store service.

    This class provides a client for the vector store service, which is used to
    check the status of the embeddings.

    Attributes:
        base_url: The base URL of the vector store service.
    """

    def __init__(self, base_url: str = "http://localhost:8088") -> None:
        """Initialise the vector store client.

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
            logger.info("Attempting to connect to vector store", url=url)
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                logger.info(
                    "Vector store response status",
                    status_code=str(response.status_code),
                )
                response.raise_for_status()
                result = response.json()
                logger.info("Vector store response", result=str(result))
                return result
        except httpx.HTTPError as e:
            logger.error("Failed to connect to vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to vector store: {e!s}",
            ) from e
        except Exception as e:
            logger.error("Unexpected error connecting to vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error connecting to vector store: {e!s}",
            ) from e

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
            HTTPException: If there is an error searching the vector store.
        """
        try:
            url = f"{self.base_url}/v1/sic-vector-store/search-index"
            logger.info("Attempting to search vector store", url=url)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "industry_descr": industry_descr,
                        "job_title": job_title,
                        "job_description": job_description,
                    },
                )
                logger.info(
                    "Vector store response status",
                    status_code=str(response.status_code),
                )
                response.raise_for_status()
                result = response.json()
                logger.info("Vector store response", result=str(result))
                return result["results"]
        except httpx.HTTPError as e:
            logger.error("Failed to search vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to search vector store: {e!s}",
            ) from e
        except Exception as e:
            logger.error("Unexpected error searching vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching vector store: {e!s}",
            ) from e
