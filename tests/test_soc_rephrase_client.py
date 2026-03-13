"""Tests for the SOC rephrase client."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from api.services.soc_rephrase_client import SOCRephraseClient


class TestSOCRephraseClient:
    """Test cases for the SOC rephrase client."""

    # --- Data loading and behaviour tests (mirroring SIC) ---

    def test_init_with_custom_path(self):
        """Initialisation with a custom SOC rephrase data path."""
        custom_path = "/custom/path/rephrased_soc.csv"

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [
                (0, {"soc_code": "1111", "rephrased_description": "Farm workers"}),
                (
                    1,
                    {
                        "soc_code": "2112",
                        "rephrased_description": "Science professionals",
                    },
                ),
            ]

            SOCRephraseClient(data_path=custom_path)

            mock_read_csv.assert_called_once_with(custom_path, dtype={"soc_code": str})

    def test_init_with_config_path(self):
        """Initialisation using package data path (via resolve_package_data_path)."""
        with patch("pandas.read_csv") as mock_read_csv, patch(
            "api.services.soc_rephrase_client.resolve_package_data_path"
        ) as mock_resolve:
            mock_resolve.return_value = "/package/path/example_rephrased_soc_data.csv"
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [
                (0, {"soc_code": "1111", "rephrased_description": "Farm workers"}),
            ]

            SOCRephraseClient()

            mock_read_csv.assert_called_once()
            call_path = mock_read_csv.call_args[0][0]
            assert "/package/path/example_rephrased_soc_data.csv" in call_path

    def test_init_with_soc_library_path(self):
        """Initialisation uses soc-classification-library example data path."""
        with patch("pandas.read_csv") as mock_read_csv, patch(
            "api.services.soc_rephrase_client.resolve_package_data_path"
        ) as mock_resolve:
            mock_resolve.return_value = "/package/path/example_rephrased_soc_data.csv"
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [
                (0, {"soc_code": "1111", "rephrased_description": "Farm workers"}),
            ]

            SOCRephraseClient()

            mock_read_csv.assert_called_once()
            assert mock_read_csv.call_args[1]["dtype"] == {"soc_code": str}
            call_path = mock_read_csv.call_args[0][0]
            assert "/package/path/example_rephrased_soc_data.csv" in call_path
            mock_resolve.assert_called_once_with(
                "occupational_classification.data",
                "example_rephrased_soc_data.csv",
            )

    def test_load_rephrase_data_success(self):
        """Successful loading of SOC rephrase data."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
            {"soc_code": "2112", "rephrased_description": "Science professionals"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = list(enumerate(test_data))

            client = SOCRephraseClient()

            assert client.get_rephrased_description("1111") == "Farm workers"
            assert client.get_rephrased_description("2112") == "Science professionals"
            expected_count = 2
            assert client.get_rephrased_count() == expected_count

    @pytest.mark.parametrize(
        ("setup_kind", "expected_message_fragment"),
        [
            ("missing_columns", "CSV file must contain columns"),
            ("file_not_found", "Rephrased SOC data file not found"),
        ],
    )
    def test_load_rephrase_data_error_cases(
        self, setup_kind: str, expected_message_fragment: str
    ):
        """Loading data error cases raise HTTPException with a 500 status."""
        with patch("pandas.read_csv") as mock_read_csv:
            if setup_kind == "missing_columns":
                mock_df = mock_read_csv.return_value
                mock_df.columns = [
                    "soc_code",
                    "wrong_column",
                ]
            else:
                mock_read_csv.side_effect = FileNotFoundError("File not found")

            with pytest.raises(HTTPException) as exc_info:
                SOCRephraseClient()

            expected_status_code = 500
            assert exc_info.value.status_code == expected_status_code
            assert expected_message_fragment in str(exc_info.value.detail)

    def test_get_rephrased_description(self):
        """Get rephrased description for a SOC code."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SOCRephraseClient()

            assert client.get_rephrased_description("1111") == "Farm workers"
            assert client.get_rephrased_description("9999") is None

    def test_has_rephrased_description(self):
        """Check if a rephrased description exists."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SOCRephraseClient()

            assert client.has_rephrased_description("1111") is True
            assert client.has_rephrased_description("9999") is False

    def test_get_rephrased_count(self):
        """Get the count of rephrased descriptions."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
            {"soc_code": "2112", "rephrased_description": "Science professionals"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = list(enumerate(test_data))

            client = SOCRephraseClient()

            expected_count = 2
            assert client.get_rephrased_count() == expected_count

    def test_process_classification_response(self):
        """Process SOC response with main code and candidates."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
            {"soc_code": "2112", "rephrased_description": "Science professionals"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = list(enumerate(test_data))

            client = SOCRephraseClient()

            response_data = {
                "soc_code": "1111",
                "soc_description": "Old description",
                "soc_candidates": [
                    {
                        "soc_code": "2112",
                        "soc_descriptive": "Old candidate",
                        "likelihood": 0.8,
                    },
                    {
                        "soc_code": "9999",
                        "soc_descriptive": "Unchanged candidate",
                        "likelihood": 0.2,
                    },
                ],
            }

            processed = client.process_classification_response(response_data)

            assert processed["soc_description"] == "Farm workers"
            candidates = processed["soc_candidates"]
            assert candidates[0]["soc_descriptive"] == "Science professionals"
            assert candidates[1]["soc_descriptive"] == "Unchanged candidate"

    def test_process_classification_response_no_rephrased(self):
        """Processing response when no rephrased descriptions exist for codes."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SOCRephraseClient()

            response_data = {
                "soc_code": "9999",
                "soc_description": "Some other occupation",
                "soc_candidates": [],
            }

            processed = client.process_classification_response(response_data)
            assert processed["soc_description"] == "Some other occupation"

    def test_process_classification_response_empty_data(self):
        """Processing response with empty or None data."""
        test_data = [
            {"soc_code": "1111", "rephrased_description": "Farm workers"},
        ]

        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = mock_read_csv.return_value
            mock_df.columns = ["soc_code", "rephrased_description"]
            mock_df.iterrows.return_value = [(0, row) for row in test_data]

            client = SOCRephraseClient()

            response_data: dict[str, object] = {}
            processed = client.process_classification_response(response_data)
            assert not processed

            response_data = {
                "soc_code": None,
                "soc_description": None,
                "soc_candidates": None,
            }
            processed = client.process_classification_response(response_data)
            assert processed == response_data
