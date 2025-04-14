"""Module that provides the SIC lookup client service for the Survey Assist API.

This module contains the SIC lookup client service that interfaces with the
SIC Classification Library to perform SIC code lookups.
"""

from pathlib import Path

from industrial_classification.lookup.sic_lookup import SICLookup


class SICLookupClient:
    """Client for performing SIC code lookups.

    This class provides a simplified interface to the SIC Classification Library's
    lookup functionality. It handles the initialization of the lookup service and
    provides methods for performing SIC code lookups.

    Attributes:
        lookup_service (SICLookup): The underlying SIC lookup service.
    """

    def __init__(self, data_path: str | None = None):
        """Initialize the SIC lookup client.

        Args:
            data_path (str | None, optional): Path to the SIC codes data file.
                If None, will try to find the data file in the package directory.
                Defaults to None.

        Raises:
            FileNotFoundError: If the data file cannot be found.
        """
        resolved_path: str | None = None
        if data_path is None:
            # Try to find the data file in the package directory
            package_dir = Path(__file__).parent.parent.parent
            test_path = package_dir / "data" / "sic_codes.csv"

            if test_path.exists():
                resolved_path = str(test_path)
            else:
                # Try the default path from the library
                default_path = Path(
                    "../sic-classification-library/src/industrial_classification/data/"
                    "sic_knowledge_base_utf8.csv"
                )
                if default_path.exists():
                    resolved_path = str(default_path)
                else:
                    raise FileNotFoundError(
                        f"Could not find SIC data file. Tried: {test_path} and {default_path}"
                    )
        else:
            resolved_path = data_path

        if resolved_path is None:
            raise FileNotFoundError("No valid data path provided")

        self.lookup_service = SICLookup(resolved_path)

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
