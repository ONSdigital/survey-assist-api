"""Tests for the /soc-lookup endpoint."""

from unittest.mock import MagicMock

from fastapi import status
from fastapi.testclient import TestClient

from api.main import app
from api.routes.v1.soc_lookup import get_lookup_client


def _setup_soc_lookup_override(mock_client):
    """Helper to override the SOC lookup dependency with a mock."""
    app.dependency_overrides[get_lookup_client] = lambda: mock_client


def test_soc_lookup_exact_match():
    """Test the SOC Lookup functionality with an exact match."""
    mock_client = MagicMock()
    mock_client.get_result.return_value = {
        "description": "senior officials and managers",
        "code": "1111",
        "code_major_group": "1",
    }
    _setup_soc_lookup_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/soc-lookup",
        params={"description": "senior officials and managers", "similarity": "false"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["code"] == "1111"
    assert body["description"] == "senior officials and managers"
    mock_client.get_result.assert_called_once_with(
        "senior officials and managers", False
    )


def test_soc_lookup_similarity():
    """Test the SOC Lookup functionality with similarity search enabled."""
    mock_client = MagicMock()
    mock_client.get_result.return_value = {
        "description": "senior officials and managers",
        "code": "1111",
        "code_major_group": "1",
        "potential_matches": {
            "descriptions": [
                "senior officials and managers",
                "production or operations managers",
            ],
            "codes": ["1111", "1112"],
        },
    }
    _setup_soc_lookup_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/soc-lookup",
        params={"description": "senior officials", "similarity": "true"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["code"] == "1111"
    assert "potential_matches" in body
    assert body["potential_matches"]["codes"] == ["1111", "1112"]
    mock_client.get_result.assert_called_once_with("senior officials", True)


def test_soc_lookup_no_description():
    """Test the SOC Lookup functionality when no description is provided."""
    mock_client = MagicMock()
    _setup_soc_lookup_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/soc-lookup",
        params={"description": "", "similarity": "false"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["detail"] == "Description cannot be empty"


def test_soc_lookup_not_found():
    """Test the SOC Lookup functionality when no result is found."""
    mock_client = MagicMock()
    mock_client.get_result.return_value = None
    _setup_soc_lookup_override(mock_client)

    client = TestClient(app)
    response = client.get(
        "/v1/survey-assist/soc-lookup",
        params={"description": "unknown title", "similarity": "false"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body["detail"] == "No SOC code found for description: unknown title"
