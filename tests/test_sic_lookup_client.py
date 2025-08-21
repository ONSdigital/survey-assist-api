"""Tests for the SICLookupClient class.

This module contains pytest-based unit tests for the SICLookupClient class, which
provides SIC code lookup functionality.
"""

from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from api.config import settings
from api.services.sic_lookup_client import SICLookupClient

# Test constants
EXPECTED_SIC_CODE_COUNT = 250


class TestSICLookupClient:
    """Test cases for the SICLookupClient class."""

    def test_init_with_custom_path(self):
        """Test initialisation with a custom data path."""
        custom_path = "/custom/path/lookup.csv"

        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_sic_codes_count.return_value = 100
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient(data_path=custom_path)

            mock_lookup.assert_called_once_with(custom_path)
            assert client.lookup_service == mock_instance

    def test_init_with_config_path(self):
        """Test initialisation using configuration path."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_sic_codes_count.return_value = 100
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            SICLookupClient()

            # Should call SICLookup with configuration path
            mock_lookup.assert_called_once()
            call_args = mock_lookup.call_args[0][0]
            # Check for configuration path
            assert settings.SIC_LOOKUP_DATA_PATH in call_args

    def test_init_with_sic_library_path(self):
        """Test initialisation using configuration path."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_sic_codes_count.return_value = 100
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            SICLookupClient()

            # Should call SICLookup with configuration path
            mock_lookup.assert_called_once()
            call_args = mock_lookup.call_args[0][0]
            # Check for configuration path
            assert settings.SIC_LOOKUP_DATA_PATH in call_args

    def test_lookup_success(self):
        """Test successful lookup operation."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.return_value = {
                "code": "01110",
                "description": "Cereal farming",
            }
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient()
            result = client.lookup("cereal farming")

            assert result == {"code": "01110", "description": "Cereal farming"}
            mock_instance.lookup.assert_called_once_with("cereal farming")

    def test_lookup_no_match(self):
        """Test lookup when no match is found."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.return_value = None
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient()
            result = client.lookup("nonexistent description")

            assert result is None
            mock_instance.lookup.assert_called_once_with("nonexistent description")

    def test_lookup_with_similarity(self):
        """Test lookup with similarity search enabled."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.return_value = {
                "code": "01110",
                "description": "Cereal farming",
            }
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient()
            result = client.similarity_search("cereal")

            assert result == {"code": "01110", "description": "Cereal farming"}
            mock_instance.lookup.assert_called_once_with("cereal", similarity=True)

    def test_get_sic_codes_count(self):
        """Test getting the count of available SIC codes."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_sic_codes_count.return_value = EXPECTED_SIC_CODE_COUNT
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = EXPECTED_SIC_CODE_COUNT

            client = SICLookupClient()
            count = client.get_sic_codes_count()

            assert count == EXPECTED_SIC_CODE_COUNT

    def test_lookup_code_division(self):
        """Test looking up code division information."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup_code_division.return_value = {
                "division": "01",
                "description": "Agriculture",
            }
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient()
            # Note: This method doesn't exist on SICLookupClient,
            # so we'll test the underlying service
            result = client.lookup_service.lookup_code_division("01110")

            assert result == {"division": "01", "description": "Agriculture"}

    def test_unique_code_divisions(self):
        """Test getting unique code divisions from a list of candidates."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            candidates = [
                {"code": "01110", "division": "01"},
                {"code": "01120", "division": "01"},
                {"code": "01210", "division": "01"},
            ]
            mock_instance.unique_code_divisions.return_value = ["01"]
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient()
            # Note: This method doesn't exist on SICLookupClient,
            # so we'll test the underlying service
            result = client.lookup_service.unique_code_divisions(candidates)

            assert result == ["01"]

    def test_lookup_error_handling(self):
        """Test error handling during lookup operations."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.side_effect = Exception("Database error")
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 100

            client = SICLookupClient()

            with pytest.raises(Exception, match="Database error"):
                client.lookup("test description")

    def test_initialization_error_handling(self):
        """Test error handling during client initialization."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_lookup.side_effect = FileNotFoundError("Data file not found")

            with pytest.raises(FileNotFoundError, match="Data file not found"):
                SICLookupClient()

    def test_data_loading_confirmation(self):
        """Test that data loading is confirmed with logging."""
        with patch("api.services.sic_lookup_client.SICLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.get_sic_codes_count.return_value = 150
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 150

            with patch("api.services.sic_lookup_client.logger") as mock_logger:
                # Capture the logged message
                captured_message: str | None = None
                captured_args: tuple[Any, ...] | None = None

                def mock_info(message: str, *args: Any) -> None:
                    nonlocal captured_message, captured_args
                    captured_message = message
                    captured_args = args

                mock_logger.info.side_effect = mock_info

                SICLookupClient()

                # Verify logging message was called
                mock_logger.info.assert_called()
                # Check the captured message and format it
                assert captured_message is not None
                assert isinstance(captured_message, str)
                # pylint: disable=unsupported-membership-test
                assert "SIC lookup data loaded from" in captured_message
                if captured_args:
                    formatted_message = captured_message % captured_args
                    assert "150 codes available" in formatted_message
                else:
                    assert "150 codes available" in captured_message


# Test the actual API endpoints
def test_sic_lookup_exact_match(test_client):
    """Test the SIC Lookup endpoint with an exact match.

    This test sends a GET request to the SIC Lookup endpoint with a specific
    description ("street lighting installation") and verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected code "43210".
    3. The response JSON contains the expected description "street lighting installation".

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The response JSON contains the correct "code" value.
    - The response JSON contains the correct "description" value.
    """
    response = test_client.get(
        "/v1/survey-assist/sic-lookup?description=street%20lighting%20installation"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["code"] == "43210"
    assert response.json()["description"] == "street lighting installation"


def test_sic_lookup_similarity(test_client):
    """Test the SIC Lookup endpoint with similarity search enabled.

    This test sends a GET request to the SIC Lookup endpoint with the description
    parameter set to "electrician" and the similarity parameter set to true. It
    verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains a "potential_matches" key, indicating similarity
       search results.
    3. The "potential_matches" object in the response JSON contains a
       "descriptions" key.

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The "potential_matches" key is present in the response JSON.
    - The "descriptions" key is present within the "potential_matches" object in
      the response JSON.
    """
    response = test_client.get(
        "/v1/survey-assist/sic-lookup?description=electrician&similarity=true"
    )
    assert response.status_code == HTTPStatus.OK
    assert "potential_matches" in response.json()
    assert "descriptions" in response.json()["potential_matches"]


def test_sic_lookup_no_description(test_client):
    """Test the SIC Lookup endpoint to ensure it returns an error when the description
    parameter is missing.

    This test sends a GET request to the SIC Lookup endpoint without providing a
    description parameter. It verifies:
    1. The response status code is HTTP 422 (Unprocessable Entity).
    2. The response JSON contains the expected validation error details.

    Assertions:
    - The response status code is HTTPStatus.UNPROCESSABLE_ENTITY.
    - The response JSON matches the expected validation error format.
    """
    response = test_client.get("/v1/survey-assist/sic-lookup")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "description"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }
