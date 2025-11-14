"""Firestore client initialisation and access helpers."""

from __future__ import annotations

from typing import Any

from firebase_admin import firestore, initialize_app  # type: ignore
from google.api_core.exceptions import ServiceUnavailable
from google.api_core.retry import Retry
from survey_assist_utils.logging import get_logger

from api.config import settings

_db_client: Any = None
logger = get_logger(__name__)

# Configure retry for Firestore operations
retry_config = Retry(
    predicate=lambda exc: isinstance(exc, ServiceUnavailable),
    initial=0.5,
    maximum=10.0,
    multiplier=1.5,
    deadline=30.0,
    on_error=lambda exc: logger.warning(f"Retrying due to: {exc}"),
)


def init_firestore_client() -> None:
    """Initialise the global Firestore client if configuration is provided.

    This should be called once on application startup.
    """
    global _db_client  # noqa: PLW0603  # pylint: disable=global-statement
    if settings.FIRESTORE_DB_ID is None:
        # Firestore not configured
        _db_client = None
        return

    app_options = {}
    if settings.GCP_PROJECT_ID:
        app_options["projectId"] = settings.GCP_PROJECT_ID

    app = initialize_app(options=app_options if app_options else None)
    _db_client = firestore.client(app=app, database_id=settings.FIRESTORE_DB_ID)


def get_firestore_client() -> Any:
    """Get the initialised Firestore client.

    Raises:
        RuntimeError: If the client has not been initialised.
    """
    if _db_client is None:
        raise RuntimeError(
            "Firestore client not initialised or FIRESTORE_DB_ID not set"
        )
    return _db_client
