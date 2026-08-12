"""Tests for the base vector store client behaviour."""

from http import HTTPStatus
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from api.services.sic_vector_store_client import SICVectorStoreClient
from api.services.token_provider import TokenProviderError


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_status_passes_provider_headers_to_http_client() -> None:
    """Pass authentication headers to the status request."""
    token_provider = AsyncMock()
    token_provider.get_headers.return_value = {"Authorization": "Bearer test-token"}

    response = Mock()
    response.json.return_value = {"status": "ready"}
    response.raise_for_status.return_value = None

    http_client = AsyncMock()
    http_client.get.return_value = response

    client = SICVectorStoreClient(
        http_client=http_client,
        token_provider=token_provider,
    )

    assert await client.get_status() == {"status": "ready"}

    token_provider.get_headers.assert_awaited_once_with()
    http_client.get.assert_awaited_once_with(
        "http://localhost:8088/v1/sic-vector-store/status",
        headers={"Authorization": "Bearer test-token"},
    )


@pytest.mark.api
@pytest.mark.asyncio
async def test_search_passes_provider_headers_to_http_client() -> None:
    """Pass authentication headers to the search request."""
    token_provider = AsyncMock()
    token_provider.get_headers.return_value = {"Authorization": "Bearer test-token"}

    expected_results = [
        {
            "code": "86101",
            "descriptive": "Hospital activities",
            "likelihood": 0.95,
        }
    ]

    response = Mock()
    response.json.return_value = {"results": expected_results}
    response.raise_for_status.return_value = None

    http_client = AsyncMock()
    http_client.post.return_value = response

    client = SICVectorStoreClient(
        http_client=http_client,
        token_provider=token_provider,
    )

    result = await client.search(
        industry_descr="Health care provider",
        job_title="Nurse",
        job_description="Provides patient care",
        correlation_id="test-correlation-id",
    )

    assert result == expected_results
    token_provider.get_headers.assert_awaited_once_with()
    http_client.post.assert_awaited_once_with(
        "http://localhost:8088/v1/sic-vector-store/search-index",
        json={
            "industry_descr": "Health care provider",
            "job_title": "Nurse",
            "job_description": "Provides patient care",
        },
        headers={"Authorization": "Bearer test-token"},
    )


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_status_maps_token_provider_error_to_503() -> None:
    """Return a sanitised 503 when status authentication fails."""
    token_provider = AsyncMock()
    token_provider.get_headers.side_effect = TokenProviderError(
        "Permission iam.serviceAccounts.getOpenIdToken denied"
    )

    http_client = AsyncMock()

    client = SICVectorStoreClient(
        http_client=http_client,
        token_provider=token_provider,
    )

    with pytest.raises(HTTPException) as exc_info:
        await client.get_status()

    assert exc_info.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert exc_info.value.detail == ("Unable to authenticate to SIC vector store")
    assert "getOpenIdToken" not in str(exc_info.value.detail)

    token_provider.get_headers.assert_awaited_once_with()
    http_client.get.assert_not_awaited()


@pytest.mark.api
@pytest.mark.asyncio
async def test_search_maps_token_provider_error_to_503() -> None:
    """Return a sanitised 503 when search authentication fails."""
    token_provider = AsyncMock()
    token_provider.get_headers.side_effect = TokenProviderError(
        "Permission iam.serviceAccounts.getOpenIdToken denied"
    )

    http_client = AsyncMock()

    client = SICVectorStoreClient(
        http_client=http_client,
        token_provider=token_provider,
    )

    with pytest.raises(HTTPException) as exc_info:
        await client.search(
            industry_descr="Health care provider",
            job_title="Nurse",
            job_description="Provides patient care",
            correlation_id="test-correlation-id",
        )

    assert exc_info.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert exc_info.value.detail == ("Unable to authenticate to SIC vector store")
    assert "getOpenIdToken" not in str(exc_info.value.detail)

    token_provider.get_headers.assert_awaited_once_with()
    http_client.post.assert_not_awaited()
