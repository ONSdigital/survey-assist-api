"""Tests for the SIC rephrase client."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

from api.services.sic_rephrase_client import SICRephraseClient

logger = get_logger(__name__)


class TestSICRephraseClient:
    """Test cases for the SIC rephrase client."""

    def test_init_with_custom_path(self):
        """Test initialisation with a custom data path."""
        custom_path = "/custom/path/rephrased.csv"

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [
                (0, {"sic_code": "01120", "reviewed_description": "Rice farming"}),
                (1, {"sic_code": "01110", "reviewed_description": "Cereal farming"}),
            ]

            SICRephraseClient(data_path=custom_path)

            mock_read_csv.assert_called_once_with(custom_path, dtype={"sic_code": str})

    def test_init_with_hardcoded_path(self):
        """Test initialisation using hardcoded path (no environment variable)."""
        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [
                (0, {"sic_code": "01120", "reviewed_description": "Rice farming"}),
            ]

            SICRephraseClient()

            # Should call pandas.read_csv with hardcoded SIC library path
            mock_read_csv.assert_called_once()
            call_args = mock_read_csv.call_args[0][0]
            assert "sic-classification-library" in call_args
            assert "example_rephrased_sic_data.csv" in call_args

    def test_init_with_sic_library_path(self):
        """Test initialisation using SIC classification library path."""
        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [
                (0, {"sic_code": "01120", "reviewed_description": "Rice farming"}),
            ]

            SICRephraseClient()

            # Should call pandas.read_csv with SIC library path
            mock_read_csv.assert_called_once()
            call_args = mock_read_csv.call_args[0][0]
            assert "sic-classification-library" in call_args
            assert "example_rephrased_sic_data.csv" in call_args

    def test_load_rephrase_data_success(self):
        """Test successful loading of rephrase data."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
            {"sic_code": "01110", "reviewed_description": "Cereal farming"},
            {"sic_code": "01130", "reviewed_description": "Vegetable farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = list(enumerate(test_data))

            client = SICRephraseClient()

            # Test that data was loaded correctly
            assert client.get_rephrased_description("01120") == "Rice farming"
            assert client.get_rephrased_description("01110") == "Cereal farming"
            assert client.get_rephrased_description("01130") == "Vegetable farming"
            expected_count = 3
            assert client.get_rephrased_count() == expected_count

    def test_load_rephrase_data_missing_columns(self):
        """Test loading data with missing required columns."""
        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = [
                "sic_code",
                "wrong_column",
            ]  # Missing reviewed_description

            with pytest.raises(HTTPException) as exc_info:
                SICRephraseClient()

            expected_status_code = 500
            assert exc_info.value.status_code == expected_status_code
            assert "CSV file must contain columns" in str(exc_info.value.detail)

    def test_load_rephrase_data_file_not_found(self):
        """Test handling of missing data file."""
        with patch("pandas.read_csv") as mock_read_csv:
            mock_read_csv.side_effect = FileNotFoundError("File not found")

            with pytest.raises(HTTPException) as exc_info:
                SICRephraseClient()

            expected_status_code = 500
            assert exc_info.value.status_code == expected_status_code
            assert "Rephrased SIC data file not found" in str(exc_info.value.detail)

    def test_get_rephrased_description(self):
        """Test getting rephrased description for a SIC code."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SICRephraseClient()

            # Test existing SIC code
            assert client.get_rephrased_description("01120") == "Rice farming"

            # Test non-existing SIC code
            assert client.get_rephrased_description("99999") is None

            # Test 4-digit code - should pad to 5 digits (same as SIC lookup logic)
            assert client.get_rephrased_description("1120") == "Rice farming"

    def test_has_rephrased_description(self):
        """Test checking if a rephrased description exists."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SICRephraseClient()

            # Test existing SIC code
            assert client.has_rephrased_description("01120") is True

            # Test non-existing SIC code
            assert client.has_rephrased_description("99999") is False

    def test_get_rephrased_count(self):
        """Test getting the count of rephrased descriptions."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
            {"sic_code": "01110", "reviewed_description": "Cereal farming"},
            {"sic_code": "01130", "reviewed_description": "Vegetable farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = list(enumerate(test_data))

            client = SICRephraseClient()

            expected_count = 3
            assert client.get_rephrased_count() == expected_count

    def test_process_classification_response(self):
        """Test processing classification response with rephrased descriptions."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
            {"sic_code": "01110", "reviewed_description": "Cereal farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = list(enumerate(test_data))

            client = SICRephraseClient()

            # Test response with main SIC code and candidates
            response_data = {
                "sic_code": "01120",
                "sic_description": "Growing of rice",
                "sic_candidates": [
                    {
                        "sic_code": "01110",
                        "sic_descriptive": "Growing of cereals",
                        "likelihood": 0.8,
                    },
                    {
                        "sic_code": "99999",  # No rephrased version
                        "sic_descriptive": "Some other activity",
                        "likelihood": 0.2,
                    },
                ],
            }

            processed_response = client.process_classification_response(response_data)

            # Check that main SIC description was rephrased
            assert processed_response["sic_description"] == "Rice farming"

            # Check that candidate descriptions were rephrased where available
            candidates = processed_response["sic_candidates"]
            assert candidates[0]["sic_descriptive"] == "Cereal farming"
            assert (
                candidates[1]["sic_descriptive"] == "Some other activity"
            )  # Unchanged

    def test_process_classification_response_no_rephrased(self):
        """Test processing response when no rephrased descriptions are available."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SICRephraseClient()

            # Test response with SIC code that has no rephrased version
            response_data = {
                "sic_code": "99999",
                "sic_description": "Some other activity",
                "sic_candidates": [],
            }

            processed_response = client.process_classification_response(response_data)

            # Check that description remains unchanged
            assert processed_response["sic_description"] == "Some other activity"

    def test_process_classification_response_empty_data(self):
        """Test processing response with empty or missing data."""
        test_data = [
            {"sic_code": "01120", "reviewed_description": "Rice farming"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["sic_code", "reviewed_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SICRephraseClient()

            # Test with empty response
            response_data = {}
            processed_response = client.process_classification_response(response_data)
            assert not processed_response

            # Test with None values
            response_data = {
                "sic_code": None,
                "sic_description": None,
                "sic_candidates": None,
            }
            processed_response = client.process_classification_response(response_data)
            assert processed_response == response_data
