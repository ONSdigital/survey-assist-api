"""SAYT client service for SIC description suggestions in the Survey Assist API."""

from pathlib import Path

from industrial_classification_utils.sayt import SAYTSuggester
from survey_assist_utils.logging import get_logger

from api.services.package_utils import resolve_package_data_path

logger = get_logger(__name__)


class SICSaytClient:
    """Client wrapper for SIC search-as-you-type suggestions.

    The underlying suggester can be expensive to build, so it is initialised lazily
    on first use unless it is explicitly warmed during application startup.
    """

    def __init__(self, data_path: str | None = None) -> None:
        """Initialise the SAYT client.

        Args:
            data_path: Optional path to the SIC lookup CSV used as the SAYT corpus.
                If not provided, the default packaged example dataset is used.
        """
        resolved_path = self._get_default_path() if data_path is None else data_path
        if isinstance(resolved_path, Path):
            resolved_path = str(resolved_path)

        self._data_path = resolved_path
        self._suggester: SAYTSuggester | None = None

    def _get_default_path(self) -> str:
        """Get the default path to the SIC lookup CSV used for SAYT suggestions."""
        return resolve_package_data_path(
            "industrial_classification.data", "example_sic_lookup_data.csv"
        )

    def _get_suggester(self) -> SAYTSuggester:
        """Return the cached suggester, constructing it on first use."""
        if self._suggester is None:
            self._suggester = SAYTSuggester.from_csv(
                self._data_path,
                search_text_col="description",
                display_text_col="description",
            )
            logger.info("Loaded SIC SAYT corpus", data_path=self._data_path)

        return self._suggester

    def get_suggestions(
        self, description: str | None, num_suggestions: int | None = None
    ) -> list[str]:
        """Return SAYT suggestions for the provided partial description.

        Args:
            description: Free-text SIC description prefix entered by the user.
            num_suggestions: Optional maximum number of suggestions to return.

        Returns:
            A list of suggestion strings.
        """
        return self._get_suggester().suggest(description, num_suggestions)
