"""Token provider."""

from __future__ import annotations

import asyncio
from typing import Protocol

from google.auth.credentials import Credentials, TokenState
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class TokenProviderError(RuntimeError):
    """Raised when authentication headers cannot be obtained."""


class TokenProvider(Protocol):  # pylint: disable=too-few-public-methods
    """Provides headers for outbound vector-store requests."""

    async def get_headers(self) -> dict[str, str]:
        """Return headers to send with the request."""


class GoogleIDTokenProvider:  # pylint: disable=too-few-public-methods
    """Provide cached Google ID tokens for one target audience."""

    def __init__(self, audience: str) -> None:
        self._request = Request()
        self._credentials: Credentials = id_token.fetch_id_token_credentials(
            audience,
            request=self._request,
        )
        logger.info("Initialised GoogleIDTokenProvider")
        self._refresh_lock = asyncio.Lock()

    async def get_headers(self) -> dict[str, str]:
        """Return an ID token, refreshing it only when necessary."""
        try:
            if self._credentials.token_state is not TokenState.FRESH:
                async with self._refresh_lock:
                    # Recheck after acquiring the lock because another request
                    # may already have refreshed the token.
                    if self._credentials.token_state is not TokenState.FRESH:
                        logger.info("Refreshing Google ID token")
                        await asyncio.to_thread(
                            self._credentials.refresh,
                            self._request,
                        )
        except GoogleAuthError as exc:
            raise TokenProviderError("Unable to obtain Google ID token") from exc

        if self._credentials.token is None:
            raise TokenProviderError("Google ID token was not available")

        return {
            "Authorization": f"Bearer {self._credentials.token}",
        }


class NoAuthTokenProvider:  # pylint: disable=too-few-public-methods
    """Token provider that deliberately disables auth for local/sidecar calls."""

    async def get_headers(self) -> dict[str, str]:
        """Return no auth headers."""
        return {}
