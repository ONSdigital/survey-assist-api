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

    def __init__(
        self,
        data_path=(
            "../sic-classification-library/src/industrial_classification/data/"
            "example_sic_lookup_data.csv"
        ),
    ):
        """Initialize the SIC lookup client.

        Args:
            data_path (str, optional): Path to the SIC lookup data file.
                Defaults to the example data file path.
        """
        self.lookup_service = SICLookup(data_path)

    def get_result(self, description, similarity=False):
        """Get the SIC lookup result for a given description.

        Args:
            description (str): The description to look up.
            similarity (bool): Whether to use similarity search.

        Returns:
            dict: The SIC lookup result.
        """
        return self.lookup_service.lookup(description, similarity)
