"""Base vector store client service for the Survey Assist API.

This module provides a base client for vector store services to eliminate code duplication.
"""

from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import httpx
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class BaseVectorStoreClient(ABC):  # pylint: disable=too-few-public-methods
    """Base client for vector store services.

    This class provides common functionality for vector store clients to eliminate
    code duplication between SIC and SOC vector store clients.

    Attributes:
        base_url: The base URL of the vector store service.
    """

    def __init__(self, base_url: str) -> None:
        """Initialise the base vector store client.

        Args:
            base_url: The base URL of the vector store service.
        """
        self.base_url = base_url

    @abstractmethod
    def get_status_url(self) -> str:
        """Get the status endpoint URL.

        Returns:
            str: The status endpoint URL.
        """

    @abstractmethod
    def get_search_url(self) -> str:
        """Get the search endpoint URL.

        Returns:
            str: The search endpoint URL.
        """

    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name for logging.

        Returns:
            str: The service name.
        """

    async def get_status(self) -> dict[str, Any]:
        """Get the status of the vector store.

        Returns:
            Dict containing the status of the vector store.

        Raises:
            HTTPException: If the request to the vector store fails.
        """
        try:
            url = self.get_status_url()
            logger.info(
                f"Attempting to check {self.get_service_name()} status", url=url
            )
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                logger.info(
                    f"{self.get_service_name()} response status",
                    status_code=str(response.status_code),
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"{self.get_service_name()} status", result=str(result))
                return result
        except httpx.HTTPError as e:
            logger.error(
                f"Failed to check {self.get_service_name()} status", error=str(e)
            )
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to check {self.get_service_name()} status: {e!s}",
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error checking {self.get_service_name()} status",
                error=str(e),
            )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking {self.get_service_name()} status: {e!s}",
            ) from e

    async def search(
        self, industry_descr: str | None, job_title: str, job_description: str
    ) -> list[dict[str, Any]]:
        """Search the vector store for similar codes.

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
            url = self.get_search_url()
            logger.info(f"Attempting to search {self.get_service_name()}", url=url)
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
                    f"{self.get_service_name()} response status",
                    status_code=str(response.status_code),
                )
                response.raise_for_status()
                result = response.json()
                logger.info(
                    f"{self.get_service_name()} search results", result=str(result)
                )
                # Handle different response formats
                if isinstance(result, dict) and "results" in result:
                    return result["results"]
                return result
        except httpx.HTTPError as e:
            logger.error(f"Failed to search {self.get_service_name()}", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to search {self.get_service_name()}: {e!s}",
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error searching {self.get_service_name()}", error=str(e)
            )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching {self.get_service_name()}: {e!s}",
            ) from e
