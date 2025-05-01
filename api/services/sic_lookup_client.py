"""SIC lookup client service for the Survey Assist API.

This module provides a client for the SIC lookup service, which is used to
look up SIC codes and descriptions.
"""

from pathlib import Path

from industrial_classification.lookup.sic_lookup import SICLookup


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
            data_path: Path to the SIC data file. If not provided, the default
                knowledge base path will be used.
        """
        # Use the provided path or default path
        if data_path is None:
            # Get the absolute path to the project root
            project_root = Path(__file__).parent.parent.parent
            resolved_path = str(
                project_root
                / "sic-classification-library/src/industrial_classification"
                / "data/sic_knowledge_base_utf8.csv"
            )
        else:
            resolved_path = data_path

        # Ensure the path is a string
        if isinstance(resolved_path, Path):
            resolved_path = str(resolved_path)

        # Initialise the SIC lookup service
        self.lookup_service = SICLookup(resolved_path)

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
