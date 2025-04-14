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

import pytest
from fastapi.testclient import TestClient

from api.main import app  # Adjust the import based on your project structure

logger = logging.getLogger(__name__)
client = TestClient(app)  # Create a test client for your FastAPI app


@pytest.mark.api
def test_read_root(test_client: TestClient):
    """Test the root endpoint of the API.

    This test sends a GET request to the root endpoint ("/") and verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected message indicating the API is running.
    """
    response = test_client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Survey Assist API is running"}


@pytest.mark.api
def test_get_config(test_client: TestClient):
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
def test_sic_lookup_exact_match(test_client: TestClient):
    """Test the SIC Lookup endpoint with an exact match.

    This test sends a GET request to the SIC Lookup endpoint with a specific
    description ("Growing of rice") and verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected keys: "code" and "description".

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The response JSON contains the "code" key.
    - The response JSON contains the "description" key.
    """
    response = test_client.get(
        "/v1/survey-assist/sic-lookup?description=Growing of rice"
    )
    assert response.status_code == HTTPStatus.OK
    assert "code" in response.json()
    assert "description" in response.json()
    assert response.json()["code"] == "01120"


@pytest.mark.api
def test_sic_lookup_similarity(test_client: TestClient):
    """Test the SIC Lookup endpoint with similarity search enabled.

    This test sends a GET request to the SIC Lookup endpoint with the description
    parameter set to "rice" and the similarity parameter set to true. It verifies:
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
        "/v1/survey-assist/sic-lookup?description=rice&similarity=true"
    )
    assert response.status_code == HTTPStatus.OK
    assert "potential_matches" in response.json()
    assert "descriptions" in response.json()["potential_matches"]


@pytest.mark.api
def test_sic_lookup_no_description(test_client: TestClient):
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
