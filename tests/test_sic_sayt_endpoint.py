"""Tests for the /sic-sayt endpoint."""

from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.main import app
from api.routes.v1.sic_sayt import get_sayt_client


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    """Ensure dependency overrides from one test do not leak into another."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _setup_sic_sayt_override(mock_client):
    """Helper to override the SIC SAYT dependency with a mock."""
    app.dependency_overrides[get_sayt_client] = lambda: mock_client


def test_sic_sayt_returns_suggestions():
    """Return suggestions for a valid partial SIC description."""
    mock_client = MagicMock()
    mock_client.get_suggestions.return_value = [
        "Street lighting installation",
        "Installation and maintenance of refrigeration",
    ]
    _setup_sic_sayt_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/sic-sayt",
        params={"description": "street", "num_suggestions": "2"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "suggestions": [
            "Street lighting installation",
            "Installation and maintenance of refrigeration",
        ]
    }
    mock_client.get_suggestions.assert_called_once_with("street", 2)


def test_sic_sayt_returns_empty_list_for_short_query():
    """Return an empty suggestion list when the SAYT client finds no matches."""
    mock_client = MagicMock()
    mock_client.get_suggestions.return_value = []
    _setup_sic_sayt_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/sic-sayt",
        params={"description": "st"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"suggestions": []}
    mock_client.get_suggestions.assert_called_once_with("st", None)


def test_sic_sayt_rejects_empty_description():
    """Reject empty descriptions with the same validation style as lookup endpoints."""
    mock_client = MagicMock()
    _setup_sic_sayt_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/sic-sayt",
        params={"description": ""},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Description cannot be empty"


def test_sic_sayt_validates_num_suggestions():
    """Reject invalid num_suggestions values via FastAPI query validation."""
    mock_client = MagicMock()
    _setup_sic_sayt_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/sic-sayt",
        params={"description": "street", "num_suggestions": "0"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
