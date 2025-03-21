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
def test_read_root():
    """Test the root endpoint of the API.

    This test sends a GET request to the root endpoint ("/") and verifies:
    1. The response status code is HTTP 200 (OK).
    2. The response JSON contains the expected message indicating the API is running.
    """
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Survey Assist API is running"}


@pytest.mark.api
def test_get_config():
    """Test the `/v1/survey-assist/config` endpoint.

    This test verifies that the endpoint returns a successful HTTP status code
    and that the response JSON contains the expected configuration for the
    `llm_model` key.

    Assertions:
    - The response status code is HTTPStatus.OK.
    - The `llm_model` in the response JSON is set to "gpt-4".
    """
    response = client.get("/v1/survey-assist/config")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["llm_model"] == "gpt-4"
