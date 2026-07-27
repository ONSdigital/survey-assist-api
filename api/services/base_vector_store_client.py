"""Base vector store client service for the Survey Assist API.

This module provides a base client for vector store services to eliminate code duplication.
"""

import time
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

import httpx
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

from api.services.token_provider import TokenProvider, TokenProviderError
from utils.survey import truncate_identifier

logger = get_logger(__name__)


class BaseVectorStoreClient(ABC):  # pylint: disable=too-few-public-methods
    """Base client for vector store services.

    This class provides common functionality for vector store clients to eliminate
    code duplication between SIC and SOC vector store clients.

    Attributes:
        base_url: The base URL of the vector store service.
    """

    def __init__(
        self,
        base_url: str,
        http_client: httpx.AsyncClient,
        token_provider: TokenProvider,
    ) -> None:
        """Initialise the base vector store client.

        Args:
            base_url: The base URL of the vector store service.
            http_client: Shared async HTTP client for outbound requests.
            token_provider: Provider for Google ID tokens.
        """
        self.base_url = base_url
        self._http_client = http_client
        self._token_provider = token_provider

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Return the shared async HTTP client used for outbound requests."""
        return self._http_client

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

            # Get authentication headers
            headers = await self._token_provider.get_headers()
            if headers:
                logger.debug(
                    f"Using authentication headers for {self.get_service_name()}"
                )

            start_time = time.perf_counter()
            logger.info(
                f"Vector store request sent - {self.get_service_name()} status",
                url=url,
            )
            response = await self._http_client.get(url, headers=headers)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                f"Vector store response received - {self.get_service_name()} status",
                status_code=str(response.status_code),
                duration_ms=str(duration_ms),
            )
            response.raise_for_status()
            result = response.json()
            # Log only summary information, not full payloads
            summary: dict[str, Any] = (
                {"keys": list(result.keys())[:5]}
                if isinstance(result, dict)
                else {"type": type(result).__name__}
            )
            logger.debug(
                f"{self.get_service_name()} status summary", summary=str(summary)
            )
            return result

        except TokenProviderError as e:
            logger.error(
                f"Failed to authenticate to {self.get_service_name()}",
                error=str(e),
            )
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=(f"Unable to authenticate to " f"{self.get_service_name()}"),
            ) from e

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to check {self.get_service_name()} status", error=str(e)
            )
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to check {self.get_service_name()} status: {e!s}",
            ) from e

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for truly unexpected errors, convert to HTTPException
            logger.error(
                f"Unexpected error checking {self.get_service_name()} status",
                error=str(e),
            )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error checking {self.get_service_name()} status: {e!s}",
            ) from e

    async def search(
        self,
        industry_descr: str | None,
        job_title: str,
        job_description: str,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search the vector store for similar codes.

        Args:
            industry_descr (str | None): The industry description.
            job_title (str): The job title.
            job_description (str): The job description.
            correlation_id (str | None): Optional correlation ID for request tracking.

        Returns:
            list[dict[str, Any]]: A list of search results, each containing a code,
                title, and distance.

        Raises:
            HTTPException: If there is an error searching the vector store.
        """
        try:
            url = self.get_search_url()

            # Get authentication headers
            headers = await self._token_provider.get_headers()
            if headers:
                logger.debug(
                    f"Using authentication headers for {self.get_service_name()}"
                )

            start_time = time.perf_counter()
            logger.info(
                f"Vector store request sent - {self.get_service_name()} search",
                url=url,
                job_title=truncate_identifier(job_title),
                job_description=truncate_identifier(job_description),
                org_description=truncate_identifier(industry_descr),
                correlation_id=correlation_id,
            )
            response = await self._http_client.post(
                url,
                json={
                    "industry_descr": industry_descr or "",
                    "job_title": job_title,
                    "job_description": job_description,
                },
                headers=headers,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                f"Vector store response received - {self.get_service_name()} search",
                status_code=str(response.status_code),
                duration_ms=str(duration_ms),
                job_title=truncate_identifier(job_title),
                job_description=truncate_identifier(job_description),
                org_description=truncate_identifier(industry_descr),
                correlation_id=correlation_id,
            )
            response.raise_for_status()
            result = response.json()
            # Log only counts/summaries, not full payloads
            if (
                isinstance(result, dict)
                and "results" in result
                and isinstance(result["results"], list)
            ):
                logger.info(
                    f"{self.get_service_name()} search results summary",
                    results_count=str(len(result["results"])),
                    job_title=truncate_identifier(job_title),
                    job_description=truncate_identifier(job_description),
                    org_description=truncate_identifier(industry_descr),
                    correlation_id=correlation_id,
                )
            elif isinstance(result, list):
                logger.info(
                    f"{self.get_service_name()} search results summary",
                    results_count=str(len(result)),
                    job_title=truncate_identifier(job_title),
                    job_description=truncate_identifier(job_description),
                    org_description=truncate_identifier(industry_descr),
                    correlation_id=correlation_id,
                )
            else:
                logger.warning(
                    f"{self.get_service_name()} search results type",
                    type=str(type(result).__name__),
                    job_title=truncate_identifier(job_title),
                    job_description=truncate_identifier(job_description),
                    org_description=truncate_identifier(industry_descr),
                    correlation_id=correlation_id,
                )
            # Handle different response formats
            if isinstance(result, dict) and "results" in result:
                return result["results"]
            return result

        except TokenProviderError as e:
            logger.error(
                f"Failed to authenticate to {self.get_service_name()}",
                error=str(e),
            )
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=(f"Unable to authenticate to " f"{self.get_service_name()}"),
            ) from e

        except httpx.HTTPError as e:
            logger.error(
                f"Failed to search {self.get_service_name()}",
                error=str(e),
                job_title=truncate_identifier(job_title),
                job_description=truncate_identifier(job_description),
                org_description=truncate_identifier(industry_descr),
                correlation_id=correlation_id,
            )
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f"Failed to search {self.get_service_name()}: {e!s}",
            ) from e

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch-all for truly unexpected errors, convert to HTTPException
            logger.error(
                f"Unexpected error searching {self.get_service_name()}",
                error=str(e),
                job_title=truncate_identifier(job_title),
                job_description=truncate_identifier(job_description),
                org_description=truncate_identifier(industry_descr),
                correlation_id=correlation_id,
            )
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error searching {self.get_service_name()}: {e!s}",
            ) from e
