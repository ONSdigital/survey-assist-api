"""Tests for Google ID token providers."""

from unittest.mock import MagicMock, patch

import pytest
from google.auth.credentials import TokenState

from api.services.google_id_token_provider import (
    GoogleIDTokenProvider,
)


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_headers_uses_fresh_cached_token() -> None:
    """Return a cached token without refreshing fresh credentials."""
    credentials = MagicMock()
    credentials.token_state = TokenState.FRESH
    credentials.token = "cached-token"

    with patch(
        "api.services.google_id_token_provider.id_token.fetch_id_token_credentials",
        return_value=credentials,
    ):
        provider = GoogleIDTokenProvider("https://vector-store.example")

    assert await provider.get_headers() == {"Authorization": "Bearer cached-token"}
    credentials.refresh.assert_not_called()


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_headers_refreshes_stale_token_once() -> None:
    """Refresh stale credentials before returning the token."""
    credentials = MagicMock()
    credentials.token_state = TokenState.STALE
    credentials.token = "stale-token"

    def refresh_credentials(_request) -> None:
        """Update the credentials as a successful refresh would."""
        credentials.token_state = TokenState.FRESH
        credentials.token = "refreshed-token"

    credentials.refresh.side_effect = refresh_credentials

    with patch(
        "api.services.google_id_token_provider.id_token.fetch_id_token_credentials",
        return_value=credentials,
    ):
        provider = GoogleIDTokenProvider("https://vector-store.example")

    headers = await provider.get_headers()

    assert headers == {"Authorization": "Bearer refreshed-token"}
    credentials.refresh.assert_called_once()
