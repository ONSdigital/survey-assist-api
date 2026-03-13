"""SOC lookup client service for the Survey Assist API.

This module provides a client for the SOC lookup service, which is used to
look up SOC codes and descriptions.
"""

import logging
from pathlib import Path

from occupational_classification.lookup.soc_lookup import SOCLookup

from api.services.package_utils import resolve_package_data_path

logger = logging.getLogger(__name__)


class SOCLookupClient:
    """Client for the SOC lookup service.

    This class provides a client for the SOC lookup service, which is used to
    look up SOC codes and descriptions.

    Attributes:
        lookup_service: The SOC lookup service instance.
    """

    def __init__(self, data_path: str | None = None) -> None:
        """Initialise the SOC lookup client.

        Args:
            data_path: Path to the SOC data file for initialisation-time configuration.
                If not provided, the default example lookup dataset path will be used.
        """
        resolved_path = self._get_default_path() if data_path is None else data_path

        if isinstance(resolved_path, Path):
            resolved_path = str(resolved_path)

        self.lookup_service = SOCLookup(resolved_path)

        logger.info(
            "Loaded %d SOC lookup codes from %s",
            self.get_soc_codes_count(),
            resolved_path,
        )

    def _get_default_path(self) -> str:
        """Get the default path to the SOC lookup data file.

        Returns:
            str: Path to the SOC lookup data file.
        """
        return resolve_package_data_path(
            "occupational_classification.example_data", "example_soc_lookup_data.csv"
        )

    def lookup(self, description: str) -> dict | None:
        """Look up a SOC code by description.

        Args:
            description: The description to look up.

        Returns:
            A dictionary containing the SOC code and description, or None if no match
            was found.
        """
        return self.lookup_service.lookup(description)

    def similarity_search(self, description: str) -> dict | None:
        """Search for similar SOC codes by description.

        Args:
            description: The description to search for.

        Returns:
            A dictionary containing potential matches, or None if no matches were
            found.
        """
        return self.lookup_service.lookup(description, similarity=True)

    def get_result(self, description: str, similarity: bool = False) -> dict:
        """Get the SOC lookup result for a given description.

        Args:
            description: The description to look up.
            similarity: Whether to use similarity search. Defaults to False.

        Returns:
            dict: The SOC lookup result.
        """
        return self.lookup_service.lookup(description, similarity)

    def get_soc_codes_count(self) -> int:
        """Get the total number of SOC codes in the lookup service.

        Returns:
            int: The total number of SOC codes available in the lookup service.
        """
        return len(self.lookup_service.data)
