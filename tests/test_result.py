"""This module contains test cases for the result endpoint of the Survey Assist API.

Functions:
    test_store_result_success():
        Tests successful result storage with valid input data.

    test_store_result_empty_fields():
        Tests error handling for empty user_id or survey.

    test_store_result_invalid_data():
        Tests error handling for invalid result data.

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - fastapi.status: Provides standard HTTP status codes for assertions.
"""

import logging

from fastapi import status
from fastapi.testclient import TestClient
from pytest import mark

from api.main import app

logger = logging.getLogger(__name__)
client = TestClient(app)


@mark.parametrize(
    "request_data,expected_status_code",
    [
        (
            {
                "user_id": "test-user-123",
                "survey": "test-survey-456",
                "job_title": "Electrician",
                "job_description": "Installing and maintaining electrical systems",
                "org_description": "Construction company",
            },
            status.HTTP_200_OK,
        ),
        (
            {
                "user_id": "",
                "survey": "test-survey-456",
                "job_title": "Electrician",
                "job_description": "Installing and maintaining electrical systems",
                "org_description": "Construction company",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            {
                "user_id": "test-user-123",
                "survey": "",
                "job_title": "Electrician",
                "job_description": "Installing and maintaining electrical systems",
                "org_description": "Construction company",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
def test_store_result(request_data, expected_status_code):
    """Test the result endpoint with various inputs.

    This test verifies the endpoint's handling of both valid and invalid requests.
    It checks:
    1. Successful result storage with valid input data.
    2. Error handling for empty user_id.
    3. Error handling for empty survey.

    Assertions:
        - The response status code matches the expected value.
        - For successful requests, the response contains the expected fields.
    """
    logger.info("Testing result endpoint with data: %s", request_data)
    response = client.post("/v1/survey-assist/result", json=request_data)
    assert response.status_code == expected_status_code

    if expected_status_code == status.HTTP_200_OK:
        response_data = response.json()
        assert "user_id" in response_data
        assert "survey" in response_data
        assert response_data["user_id"] == request_data["user_id"]
        assert response_data["survey"] == request_data["survey"]

    logger.info("Received response with status code: %d", response.status_code)


def test_store_result_invalid_data():
    """Test the endpoint's handling of invalid result data.

    This test verifies that the endpoint correctly handles invalid result data by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate validation error details.

    Assertions:
        - The response status code is 422.
    """
    request_data = {
        "user_id": "test-user-123",
        "survey": "test-survey-456",
        "job_title": None,
        "job_description": None,
        "org_description": None,
    }

    logger.info("Testing invalid result data with data: %s", request_data)
    response = client.post("/v1/survey-assist/result", json=request_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    logger.info("Received expected 422 status code")
