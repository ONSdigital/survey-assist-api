"""SIC lookup client service for the Survey Assist API.

This module provides a client for the SIC lookup service, which is used to
look up SIC codes and descriptions.
"""

import logging
import os
from pathlib import Path

from industrial_classification.lookup.sic_lookup import SICLookup

from api.services.package_utils import resolve_package_data_path

logger = logging.getLogger(__name__)


class SICLookupClient:
    """Client for the SIC lookup service.

    This class provides a client for the SIC lookup service, which is used to
    look up SIC codes and descriptions.

    Attributes:
        lookup_service: The SIC lookup service instance.
    """

    def __init__(self, data_path: str | None = None) -> None:
        """Initialise the SIC lookup client.

        Args:
            data_path: Path to the SIC data file for initialisation-time configuration.
                If not provided, the default knowledge base path will be used.
        """
        # Always call _get_default_path() to get the resolved path
        resolved_path = self._get_default_path() if data_path is None else data_path

        # Ensure the path is a string
        if isinstance(resolved_path, Path):
            resolved_path = str(resolved_path)

        # Initialise the SIC lookup service
        self.lookup_service = SICLookup(resolved_path)

        # Log confirmation of data loading
        logger.info(
            "Loaded %d SIC lookup codes from %s",
            self.get_sic_codes_count(),
            resolved_path,
        )

    def _get_default_path(self) -> str:
        """Get the default path to the SIC lookup data file.

        Returns:
            str: Path to the SIC lookup data file.
        """
        # Always use the example dataset from the package
        return resolve_package_data_path(
            "industrial_classification.data", "example_sic_lookup_data.csv"
        )

    def lookup(self, description: str) -> dict | None:
        """Look up a SIC code by description.

        Args:
            description: The description to look up.

        Returns:
            A dictionary containing the SIC code and description, or None if no match
            was found.
        """
        return self.lookup_service.lookup(description)

    def similarity_search(self, description: str) -> dict | None:
        """Search for similar SIC codes by description.

        Args:
            description: The description to search for.

        Returns:
            A dictionary containing potential matches, or None if no matches were
            found.
        """
        return self.lookup_service.lookup(description, similarity=True)

    def get_result(self, description: str, similarity: bool = False) -> dict:
        """Get the SIC lookup result for a given description.

        Args:
            description (str): The description to look up.
            similarity (bool, optional): Whether to use similarity search.
                Defaults to False.

        Returns:
            dict: The SIC lookup result.
        """
        return self.lookup_service.lookup(description, similarity)

    def get_sic_codes_count(self) -> int:
        """Get the total number of SIC codes in the lookup service.

        Returns:
            int: The total number of SIC codes available in the lookup service.
        """
        return len(self.lookup_service.data)
