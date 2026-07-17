"""Tests for the base vector store client behaviour."""

from unittest.mock import AsyncMock, Mock

import pytest

from api.services.sic_vector_store_client import SICVectorStoreClient


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
        google_id_token_provider=token_provider,
    )

    assert await client.get_status() == {"status": "ready"}

    token_provider.get_headers.assert_awaited_once_with()
    http_client.get.assert_awaited_once_with(
        "http://localhost:8088/v1/sic-vector-store/status",
        headers={"Authorization": "Bearer test-token"},
    )
