"""Vector store client service for SOC classification in the Survey Assist API.

This module provides a client for the SOC vector store service, which is used to
check the status of the SOC embeddings and perform similarity searches.
"""

from api.services.base_vector_store_client import BaseVectorStoreClient


class SOCVectorStoreClient(
    BaseVectorStoreClient
):  # pylint: disable=too-few-public-methods
    """Client for the SOC vector store service.

    This class provides a client for the SOC vector store service, which is used to
    check the status of the SOC embeddings and perform similarity searches.

    Attributes:
        base_url: The base URL of the SOC vector store service.
    """

    def __init__(self, base_url: str = "http://localhost:8089") -> None:
        """Initialise the SOC vector store client.

        Args:
            base_url: The base URL of the SOC vector store service.
        """
        super().__init__(base_url)

    def get_status_url(self) -> str:
        """Get the SOC vector store status endpoint URL.

        Returns:
            str: The SOC vector store status endpoint URL.
        """
        return f"{self.base_url}/v1/soc-vector-store/status"

    def get_search_url(self) -> str:
        """Get the SOC vector store search endpoint URL.

        Returns:
            str: The SOC vector store search endpoint URL.
        """
        return f"{self.base_url}/v1/soc-vector-store/search-index"

    def get_service_name(self) -> str:
        """Get the SOC vector store service name for logging.

        Returns:
            str: The SOC vector store service name.
        """
        return "SOC vector store"
