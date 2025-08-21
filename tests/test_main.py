"""This module contains test cases for the Survey Assist API using FastAPI's TestClient.

Functions:
    test_read_root():
        Tests the root endpoint ("/") of the API to ensure it returns a 200 OK status
        and the expected JSON response indicating the API is running.

    test_get_config():
        Tests the "/v1/survey-assist/config" endpoint to ensure it returns a 200 OK status
        and verifies that the configuration includes the expected LLM model.

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - http.HTTPStatus: Provides standard HTTP status codes for assertions.
"""

from http import HTTPStatus
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

from api.services.sic_vector_store_client import SICVectorStoreClient

logger = get_logger(__name__)


@pytest.mark.api
def test_read_root(test_client):
    """Test the root endpoint of the API.

    This test sends a GET request to the root endpoint ("/") and verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected message indicating the API is running.
    """
    response = test_client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Survey Assist API is running"}


@pytest.mark.api
def test_get_config(test_client):
    """Test the `/v1/survey-assist/config` endpoint.

    This test verifies that the endpoint returns a successful HTTP status code
    and that the response JSON contains the expected configuration for the
    `llm_model` key, embedding model, and actual prompt.

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The `llm_model` in the response JSON is set to "gemini-1.5-flash".
    - The `embedding_model` field is present and is a string.
    - The `actual_prompt` field is present and is a string.
    """
    response = test_client.get("/v1/survey-assist/config")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["llm_model"] == "gemini-1.5-flash"
    assert "embedding_model" in response.json()
    assert isinstance(response.json()["embedding_model"], str)
    # In test environment, embedding_model might be "unknown" if vector store is not available
    assert response.json()["embedding_model"] in [
        "unknown",
        "all-MiniLM-L6-v2",
        "text-embedding-ada-002",
    ]
    assert "actual_prompt" in response.json()
    assert isinstance(response.json()["actual_prompt"], str)


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_status_success():
    """Test successful status retrieval from the vector store client.

    This test mocks the HTTP client to simulate a successful response from the
    vector store service. It verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected status "ready".

    Assertions:
    - The response matches the expected status dictionary.
    """
    mock_response = AsyncMock()
    mock_response.json = Mock(return_value={"status": "ready"})
    mock_response.raise_for_status = AsyncMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client), patch(
        "api.services.base_vector_store_client.BaseVectorStoreClient._get_auth_headers",
        return_value={},
    ):
        client = SICVectorStoreClient(base_url="http://localhost:8088")
        response = await client.get_status()
        assert response == {"status": "ready"}


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_status_connection_error():
    """Test error handling for connection failures in the vector store client.

    This test mocks the HTTP client to simulate a connection error when attempting
    to reach the vector store service. It verifies:
    1. The appropriate HTTPException is raised.
    2. The exception status code is HTTP 503 (Service Unavailable).
    3. The error message contains details about the connection failure.

    Assertions:
    - The raised exception has the correct status code.
    - The error message contains the expected connection failure text.
    """
    with patch(
        "httpx.AsyncClient.get", side_effect=httpx.HTTPError("Connection error")
    ), patch(
        "api.services.base_vector_store_client.BaseVectorStoreClient._get_auth_headers",
        return_value={},
    ):
        client = SICVectorStoreClient(base_url="http://nonexistent:8088")
        with pytest.raises(HTTPException) as exc_info:
            await client.get_status()
        assert exc_info.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert "Failed to check SIC vector store status" in str(exc_info.value.detail)


@pytest.mark.api
def test_embeddings_endpoint(test_client):
    """Test the embeddings endpoint of the Survey Assist API.

    This test mocks the vector store client to simulate a successful status check
    and verifies the endpoint's response. It verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected status "ready".

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The response JSON matches the expected status dictionary.
    """
    with patch(
        "api.services.sic_vector_store_client.SICVectorStoreClient.get_status"
    ) as mock_get_status:
        mock_get_status.return_value = {"status": "ready"}
        response = test_client.get("/v1/survey-assist/embeddings")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ready"}
