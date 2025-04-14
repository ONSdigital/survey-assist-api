"""SIC Lookup Client Service.

This module provides the SIC Lookup Client service for the Survey Assist API.
It handles the interaction with the SIC classification library to perform
SIC code lookups based on business descriptions.
"""

import logging
from pathlib import Path
from typing import Optional

from industrial_classification.lookup.sic_lookup import SICLookup

logger = logging.getLogger(__name__)


class SICLookupClient:
    """Client for interacting with the SIC classification library.

    This class provides methods to look up SIC codes based on business descriptions.
    It handles the initialization of the SIC lookup service and provides methods
    to perform exact and similarity-based searches.

    Attributes:
        lookup_service (Optional[SICLookup]): The SIC lookup service instance.
    """

    def __init__(self, data_path: Optional[str] = None):
        """Initialize the SIC Lookup Client.

        Args:
            data_path (Optional[str]): Path to the SIC data file. If not provided,
                uses the default path from the SIC classification library.

        Raises:
            FileNotFoundError: If the SIC data file cannot be found.
        """
        try:
            resolved_path = data_path or str(
                Path(
                    "../sic-classification-library/src/industrial_classification/data/"
                    "sic_knowledge_base_utf8.csv"
                ).resolve()
            )
            self.lookup_service: Optional[SICLookup] = SICLookup(resolved_path)
        except FileNotFoundError:
            logger.warning(
                "SIC data file not found at %s. SIC lookup functionality will be disabled.",
                resolved_path,
            )
            self.lookup_service = None

    def lookup_sic_code(self, description: str, similarity: bool = False) -> dict:
        """Look up a SIC code based on a business description.

        Args:
            description (str): The business description to look up.
            similarity (bool, optional): Whether to perform a similarity search.
                Defaults to False.

        Returns:
            dict: A dictionary containing the SIC code and description, or
                potential matches if similarity search is enabled.

        Raises:
            RuntimeError: If the SIC lookup service is not initialized.
        """
        if self.lookup_service is None:
            raise RuntimeError("SIC lookup service is not initialized")

        if similarity:
            return self.lookup_service.lookup(description, similarity=True)
        return self.lookup_service.lookup(description, similarity=False)

    def get_sic_codes_count(self) -> int:
        """Get the total number of SIC codes in the lookup service.

        Returns:
            int: The total number of SIC codes available in the lookup service.

        Raises:
            RuntimeError: If the SIC lookup service is not initialized.
        """
        if self.lookup_service is None:
            raise RuntimeError("SIC lookup service is not initialized")
        return len(self.lookup_service.data)
