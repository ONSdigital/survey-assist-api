"""Vector store client service for SOC classification in the Survey Assist API.

This module provides a client for the SOC vector store service, which is used to
search for SOC (Standard Occupational Classification) codes based on job titles,
job descriptions, and industry descriptions.
"""

from http import HTTPStatus
from typing import Any

import httpx
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class SOCVectorStoreClient:  # pylint: disable=too-few-public-methods,duplicate-code
    """Client for the SOC vector store service.

    This class provides a client for the SOC vector store service, which is used to
    search for SOC codes based on job information.

    Attributes:
        base_url: The base URL of the SOC vector store service.
    """

    def __init__(self, base_url: str = "http://localhost:8089") -> None:
        """Initialise the SOC vector store client.

        Args:
            base_url: The base URL of the SOC vector store service.
        """
        self.base_url = base_url

    async def get_status(self) -> dict[str, str]:
        """Get the status of the SOC vector store.

        Returns:
            Dict containing the status of the SOC vector store.

        Raises:
            HTTPException: If the request to the SOC vector store fails.
        """
        try:
            url = f"{self.base_url}/v1/soc-vector-store/status"
            logger.info("Attempting to connect to SOC vector store", url=url)
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                logger.info(
                    "SOC vector store response status",
                    status_code=str(response.status_code),
                )
                response.raise_for_status()
                result = response.json()
                logger.info("SOC vector store response", result=str(result))
                return result
        except httpx.HTTPError as e:
            logger.error("Failed to connect to SOC vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to SOC vector store: {e!s}",
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error connecting to SOC vector store", error=str(e)
            )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error connecting to SOC vector store: {e!s}",
            ) from e

    async def search(
        self, industry_descr: str | None, job_title: str, job_description: str
    ) -> list[dict[str, Any]]:
        """Search the SOC vector store for similar SOC codes.

        Args:
            industry_descr (str | None): The industry description.
            job_title (str): The job title.
            job_description (str): The job description.

        Returns:
            list[dict[str, Any]]: A list of search results, each containing a code,
                title, and distance.

        Raises:
            HTTPException: If there is an error searching the SOC vector store.
        """
        try:
            url = f"{self.base_url}/v1/soc-vector-store/search-index"
            logger.info("Attempting to search SOC vector store", url=url)
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
                    "SOC vector store response status",
                    status_code=str(response.status_code),
                )
                response.raise_for_status()
                result = response.json()
                logger.info("SOC vector store response", result=str(result))
                return result["results"]
        except httpx.HTTPError as e:
            logger.error("Failed to search SOC vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to search SOC vector store: {e!s}",
            ) from e
        except Exception as e:
            logger.error("Unexpected error searching SOC vector store", error=str(e))
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching SOC vector store: {e!s}",
            ) from e
