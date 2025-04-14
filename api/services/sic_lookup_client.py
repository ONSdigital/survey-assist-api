"""Module that provides the SIC lookup client service for the Survey Assist API.

This module contains the SIC lookup client service that interfaces with the
SIC Classification Library to perform SIC code lookups.
"""

from industrial_classification.lookup.sic_lookup import SICLookup


class SICLookupClient:
    """Client for performing SIC code lookups.

    This class provides a simplified interface to the SIC Classification Library's
    lookup functionality. It handles the initialization of the lookup service and
    provides methods for performing SIC code lookups.

    Attributes:
        lookup_service (SICLookup): The underlying SIC lookup service.
    """

    def __init__(self, data_path: str = "data/sic_codes.csv"):
        """Initialize the SIC lookup client.

        Args:
            data_path (str, optional): Path to the SIC codes data file.
                Defaults to "data/sic_codes.csv".
        """
        self.lookup_service = SICLookup(data_path)

    def lookup(self, description: str, similarity: bool = False) -> dict:
        """Look up a SIC code by description.

        Args:
            description (str): The description to search for.
            similarity (bool, optional): Whether to use similarity search.
                Defaults to False.

        Returns:
            dict: A dictionary containing the SIC code and description, or
                potential matches if similarity search is enabled.

        Raises:
            ValueError: If the description is empty or None.
        """
        if not description:
            raise ValueError("Description cannot be empty or None")

        if similarity:
            return self.lookup_service.similarity_search(description)
        return self.lookup_service.exact_search(description)

    def get_sic_codes_count(self) -> int:
        """Get the total number of SIC codes in the lookup service.

        Returns:
            int: The total number of SIC codes available in the lookup service.
        """
        return len(self.lookup_service.sic_codes)
