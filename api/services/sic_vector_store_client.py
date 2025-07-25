"""Vector store client service for SIC classification in the Survey Assist API.

This module provides a client for the SIC vector store service, which is used to
check the status of the SIC embeddings and perform similarity searches.
"""

from api.services.base_vector_store_client import BaseVectorStoreClient


class SICVectorStoreClient(
    BaseVectorStoreClient
):  # pylint: disable=too-few-public-methods
    """Client for the SIC vector store service.

    This class provides a client for the SIC vector store service, which is used to
    check the status of the SIC embeddings and perform similarity searches.

    Attributes:
        base_url: The base URL of the SIC vector store service.
    """

    def __init__(self, base_url: str = "http://localhost:8088") -> None:
        """Initialise the SIC vector store client.

        Args:
            base_url: The base URL of the SIC vector store service.
        """
        super().__init__(base_url)

    def get_status_url(self) -> str:
        """Get the SIC vector store status endpoint URL.

        Returns:
            str: The SIC vector store status endpoint URL.
        """
        return f"{self.base_url}/v1/sic-vector-store/status"

    def get_search_url(self) -> str:
        """Get the SIC vector store search endpoint URL.

        Returns:
            str: The SIC vector store search endpoint URL.
        """
        return f"{self.base_url}/v1/sic-vector-store/search-index"

    def get_service_name(self) -> str:
        """Get the SIC vector store service name for logging.

        Returns:
            str: The SIC vector store service name.
        """
        return "SIC vector store"
