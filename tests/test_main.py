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

import logging
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from api.services.vector_store_client import VectorStoreClient

logger = logging.getLogger(__name__)


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
    `llm_model` key.

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The `llm_model` in the response JSON is set to "gpt-4".
    """
    response = test_client.get("/v1/survey-assist/config")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["llm_model"] == "gpt-4"


@pytest.mark.api
def test_sic_lookup_exact_match(test_client):
    """Test the SIC Lookup endpoint with an exact match.

    This test sends a GET request to the SIC Lookup endpoint with a specific
    description ("street lighting installation") and verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected code "43210".
    3. The response JSON contains the expected description "street lighting installation".

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The response JSON contains the correct "code" value.
    - The response JSON contains the correct "description" value.
    """
    response = test_client.get(
        "/v1/survey-assist/sic-lookup?description=street%20lighting%20installation"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["code"] == "43210"
    assert response.json()["description"] == "street lighting installation"


@pytest.mark.api
def test_sic_lookup_similarity(test_client):
    """Test the SIC Lookup endpoint with similarity search enabled.

    This test sends a GET request to the SIC Lookup endpoint with the description
    parameter set to "electrician" and the similarity parameter set to true. It
    verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains a "potential_matches" key, indicating similarity
       search results.
    3. The "potential_matches" object in the response JSON contains a
       "descriptions" key.

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The "potential_matches" key is present in the response JSON.
    - The "descriptions" key is present within the "potential_matches" object in
      the response JSON.
    """
    response = test_client.get(
        "/v1/survey-assist/sic-lookup?description=electrician&similarity=true"
    )
    assert response.status_code == HTTPStatus.OK
    assert "potential_matches" in response.json()
    assert "descriptions" in response.json()["potential_matches"]


@pytest.mark.api
def test_sic_lookup_no_description(test_client):
    """Test the SIC Lookup endpoint to ensure it returns an error when the description
    parameter is missing.

    This test sends a GET request to the SIC Lookup endpoint without providing a
    description parameter. It verifies:
    1. The response status code is HTTP 422 (Unprocessable Entity).
    2. The response JSON contains the expected validation error details.

    Assertions:
    - The response status code is HTTPStatus.UNPROCESSABLE_ENTITY.
    - The response JSON matches the expected validation error format.
    """
    response = test_client.get("/v1/survey-assist/sic-lookup")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "description"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_status_success():
    """Test successful status retrieval."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {"status": "ready"}
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        client = VectorStoreClient(base_url="http://localhost:8088")
        response = await client.get_status()
        assert response == {"status": "ready"}


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_status_connection_error():
    """Test error handling for connection failures."""
    with patch(
        "httpx.AsyncClient.get", side_effect=httpx.HTTPError("Connection error")
    ):
        client = VectorStoreClient(base_url="http://nonexistent:8088")
        with pytest.raises(HTTPException) as exc_info:
            await client.get_status()
        assert exc_info.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE
        assert "Failed to connect to vector store" in str(exc_info.value.detail)


@pytest.mark.api
def test_embeddings_endpoint(test_client):
    """Test the embeddings endpoint."""
    with patch(
        "api.services.vector_store_client.VectorStoreClient.get_status"
    ) as mock_get_status:
        mock_get_status.return_value = {"status": "ready"}
        response = test_client.get("/v1/survey-assist/embeddings")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"status": "ready"}
