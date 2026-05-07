"""Tests for the SICSaytClient class."""

from pathlib import Path
from unittest.mock import patch

from api.services.sic_sayt_client import SICSaytClient


class TestSICSaytClient:
    """Test cases for the SICSaytClient class."""

    def test_warm_up_builds_suggester_once(self):
        """Warm-up should build the suggester once and reuse the cached instance."""
        with patch(
            "api.services.sic_sayt_client.SAYTSuggester.from_csv"
        ) as mock_from_csv:
            client = SICSaytClient(data_path="/custom/path/lookup.csv")

            client.warm_up()
            client.warm_up()

            mock_from_csv.assert_called_once_with(
                "/custom/path/lookup.csv",
                search_text_col="description",
                display_text_col="description",
            )

    def test_get_suggestions_builds_from_custom_path(self):
        """Build the underlying suggester from a custom CSV path on first use."""
        custom_path = "/custom/path/lookup.csv"

        with patch(
            "api.services.sic_sayt_client.SAYTSuggester.from_csv"
        ) as mock_from_csv:
            mock_suggester = mock_from_csv.return_value
            mock_suggester.suggest.return_value = ["Street lighting installation"]

            client = SICSaytClient(data_path=custom_path)
            result = client.get_suggestions("street")

            assert result == ["Street lighting installation"]
            mock_from_csv.assert_called_once_with(
                custom_path,
                search_text_col="description",
                display_text_col="description",
            )
            mock_suggester.suggest.assert_called_once_with("street", None)

    def test_get_suggestions_uses_package_default_path(self):
        """Use the packaged example SIC lookup CSV when no custom path is provided."""
        with (
            patch(
                "api.services.sic_sayt_client.resolve_package_data_path"
            ) as mock_resolve,
            patch(
                "api.services.sic_sayt_client.SAYTSuggester.from_csv"
            ) as mock_from_csv,
        ):
            mock_resolve.return_value = Path(
                "/package/path/example_sic_lookup_data.csv"
            )
            mock_suggester = mock_from_csv.return_value
            mock_suggester.suggest.return_value = ["Insulating activities"]

            client = SICSaytClient()
            result = client.get_suggestions("insu", num_suggestions=3)

            assert result == ["Insulating activities"]
            mock_resolve.assert_called_once_with(
                "industrial_classification.data", "example_sic_lookup_data.csv"
            )
            mock_from_csv.assert_called_once_with(
                "/package/path/example_sic_lookup_data.csv",
                search_text_col="description",
                display_text_col="description",
            )
            mock_suggester.suggest.assert_called_once_with("insu", 3)

    def test_get_suggestions_reuses_cached_suggester(self):
        """Reuse the cached suggester after the first request."""
        with patch(
            "api.services.sic_sayt_client.SAYTSuggester.from_csv"
        ) as mock_from_csv:
            mock_suggester = mock_from_csv.return_value
            mock_suggester.suggest.side_effect = [
                ["Street lighting installation"],
                ["Construction of harbours"],
            ]

            client = SICSaytClient(data_path="/custom/path/lookup.csv")

            first_result = client.get_suggestions("street")
            second_result = client.get_suggestions("harbour", num_suggestions=2)

            assert first_result == ["Street lighting installation"]
            assert second_result == ["Construction of harbours"]
            mock_from_csv.assert_called_once()
