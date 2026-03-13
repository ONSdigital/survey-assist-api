"""Tests for the SOCLookupClient class."""

from unittest.mock import MagicMock, patch

import pytest

from api.services.soc_lookup_client import SOCLookupClient
from tests.test_lookup_client_common import (
    DataLoadingLoggingConfig,
    assert_data_loading_logging,
)

# Test constants (mirror test_sic_lookup_client.py EXPECTED_SIC_CODE_COUNT)
EXPECTED_SOC_CODE_COUNT = 10


class TestSOCLookupClient:
    """Test cases for the SOCLookupClient class."""

    def test_init_with_custom_path(self):
        """Test initialisation with a custom data path."""
        custom_path = "/custom/path/soc_lookup.csv"

        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 10

            client = SOCLookupClient(data_path=custom_path)

            mock_lookup.assert_called_once_with(custom_path)
            assert client.lookup_service == mock_instance

    def test_init_with_default_package_path(self):
        """Test initialisation using package data path."""
        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup, patch(
            "api.services.soc_lookup_client.resolve_package_data_path"
        ) as mock_resolve:
            mock_resolve.return_value = (
                "/package/path/occupational_classification/example_data/"
                "example_soc_lookup_data.csv"
            )
            mock_instance = mock_lookup.return_value
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 10

            SOCLookupClient()

            mock_lookup.assert_called_once()
            called_path = mock_lookup.call_args[0][0]
            assert "example_soc_lookup_data.csv" in called_path
            mock_resolve.assert_called_once_with(
                "occupational_classification.example_data",
                "example_soc_lookup_data.csv",
            )

    def test_lookup_success(self):
        """Test successful lookup operation."""
        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.return_value = {
                "code": "1111",
                "description": "senior officials and managers",
            }
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 10

            client = SOCLookupClient()
            result = client.lookup("senior officials and managers")

            assert result == {
                "code": "1111",
                "description": "senior officials and managers",
            }
            mock_instance.lookup.assert_called_once_with(
                "senior officials and managers"
            )

    def test_lookup_no_match(self):
        """Test lookup when no match is found."""
        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.return_value = None
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 10

            client = SOCLookupClient()
            result = client.lookup("nonexistent description")

            assert result is None
            mock_instance.lookup.assert_called_once_with("nonexistent description")

    def test_lookup_with_similarity(self):
        """Test lookup with similarity search enabled."""
        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.lookup.return_value = {
                "code": "1111",
                "description": "senior officials and managers",
            }
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = 10

            client = SOCLookupClient()
            result = client.similarity_search("senior officials")

            assert result == {
                "code": "1111",
                "description": "senior officials and managers",
            }
            mock_instance.lookup.assert_called_once_with(
                "senior officials", similarity=True
            )

    def test_get_soc_codes_count(self):
        """Test getting the count of available SOC codes."""
        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup:
            mock_instance = mock_lookup.return_value
            mock_instance.data = MagicMock()
            mock_instance.data.__len__.return_value = EXPECTED_SOC_CODE_COUNT

            client = SOCLookupClient()
            count = client.get_soc_codes_count()

            assert count == EXPECTED_SOC_CODE_COUNT

    def test_initialization_error_handling(self):
        """Test error handling during client initialization."""
        with patch("api.services.soc_lookup_client.SOCLookup") as mock_lookup:
            mock_lookup.side_effect = FileNotFoundError("SOC data file not found")

            with pytest.raises(FileNotFoundError, match="SOC data file not found"):
                SOCLookupClient()

    def test_data_loading_confirmation_logging(self):
        """Test that data loading is confirmed with logging."""
        assert_data_loading_logging(
            SOCLookupClient,
            DataLoadingLoggingConfig(
                lookup_patch_path="api.services.soc_lookup_client.SOCLookup",
                logger_patch_path="api.services.soc_lookup_client.logger",
                expected_count=7,
                codes_substring="SOC lookup codes from",
            ),
        )
