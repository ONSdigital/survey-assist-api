"""Tests for Google ID token providers."""

from unittest.mock import MagicMock, patch

import pytest
from google.auth.credentials import TokenState
from google.auth.exceptions import RefreshError

from api.services.token_provider import (
    GoogleIDTokenProvider,
    TokenProviderError,
)


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_headers_uses_fresh_cached_token() -> None:
    """Return a cached token without refreshing fresh credentials."""
    credentials = MagicMock()
    credentials.token_state = TokenState.FRESH
    credentials.token = "cached-token"

    with patch(
        "api.services.token_provider.id_token.fetch_id_token_credentials",
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
        "api.services.token_provider.id_token.fetch_id_token_credentials",
        return_value=credentials,
    ):
        provider = GoogleIDTokenProvider("https://vector-store.example")

    headers = await provider.get_headers()

    assert headers == {"Authorization": "Bearer refreshed-token"}
    credentials.refresh.assert_called_once()


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_headers_wraps_refresh_error() -> None:
    """Raise TokenProviderError when refreshing Google credentials fails."""
    credentials = MagicMock()
    credentials.token_state = TokenState.STALE
    credentials.token = None
    credentials.refresh.side_effect = RefreshError(
        "Permission iam.serviceAccounts.getOpenIdToken denied"
    )

    with patch(
        "api.services.token_provider.id_token.fetch_id_token_credentials",
        return_value=credentials,
    ):
        provider = GoogleIDTokenProvider("https://vector-store.example")

    with pytest.raises(
        TokenProviderError,
        match="Unable to obtain Google ID token",
    ) as exc_info:
        await provider.get_headers()

    assert isinstance(exc_info.value.__cause__, RefreshError)
    credentials.refresh.assert_called_once()


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_headers_raises_when_token_is_missing() -> None:
    """Raise TokenProviderError when credentials contain no ID token."""
    credentials = MagicMock()
    credentials.token_state = TokenState.FRESH
    credentials.token = None

    with patch(
        "api.services.token_provider.id_token.fetch_id_token_credentials",
        return_value=credentials,
    ):
        provider = GoogleIDTokenProvider("https://vector-store.example")

    with pytest.raises(
        TokenProviderError,
        match="Google ID token was not available",
    ):
        await provider.get_headers()

    credentials.refresh.assert_not_called()
