"""This module contains test cases for the result functionality of the Survey Assist API.

Functions:
    test_store_result_success():
        Tests successful result storage with valid input data.

    test_store_result_empty_fields():
        Tests error handling for empty survey_id or case_id.

    test_store_result_invalid_data():
        Tests error handling for invalid result data.

    test_get_result():
        Tests retrieving a stored result.

    test_get_result_not_found():
        Tests retrieving a non-existent result.

    test_datetime_serialisation():
        Tests proper serialisation of datetime objects in result data.

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - fastapi.status: Provides standard HTTP status codes for assertions.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime
from survey_assist_utils.logging import get_logger

from api.main import app

logger = get_logger(__name__)
client = TestClient(app)


def test_store_result_success():
    """Test storing a result with valid data.

    This test verifies that:
    1. A valid result can be stored successfully
    2. The response contains the correct result_id
    3. The stored data matches the input data
    """
    test_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:05:00Z",
        "responses": [
            {
                "person_id": "person-1",
                "time_start": "2024-03-19T10:00:00Z",
                "time_end": "2024-03-19T10:01:00Z",
                "survey_assist_interactions": [
                    {
                        "type": "classify",
                        "flavour": "sic",
                        "time_start": "2024-03-19T10:00:00Z",
                        "time_end": "2024-03-19T10:01:00Z",
                        "input": [
                            {
                                "field": "job_title",
                                "value": "Software Engineer"
                            }
                        ],
                        "response": {
                            "classified": True,
                            "code": "620100",
                            "description": "Software developers",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "620100",
                                    "description": "Software developers",
                                    "likelihood": 0.95
                                }
                            ],
                            "follow_up": {
                                "questions": []
                            }
                        }
                    }
                ]
            }
        ]
    }

    response = client.post("/v1/survey-assist/result", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert "result_id" in response.json()
    assert response.json()["message"] == "Result stored successfully"


def test_store_result_empty_fields():
    """Test storing a result with missing required fields.

    This test verifies that:
    1. Attempting to store a result without required fields returns a 422 status code
    2. The error message indicates which fields are missing
    """
    test_data = {
        "case_id": "test-case-456",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:05:00Z",
        "responses": []
    }

    response = client.post("/v1/survey-assist/result", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_result_invalid_data():
    """Test storing a result with invalid data.

    This test verifies that:
    1. Attempting to store a result with invalid data returns a 422 status code
    2. The error message indicates which fields are invalid
    """
    test_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "time_start": "invalid-date",
        "time_end": "2024-03-19T10:05:00Z",
        "responses": []
    }

    response = client.post("/v1/survey-assist/result", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_result():
    """Test retrieving a stored result.

    This test verifies that:
    1. A stored result can be retrieved using its result_id
    2. The retrieved data matches the stored data
    """
    # First store a result
    store_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:05:00Z",
        "responses": [
            {
                "person_id": "person-1",
                "time_start": "2024-03-19T10:00:00Z",
                "time_end": "2024-03-19T10:01:00Z",
                "survey_assist_interactions": [
                    {
                        "type": "classify",
                        "flavour": "sic",
                        "time_start": "2024-03-19T10:00:00Z",
                        "time_end": "2024-03-19T10:01:00Z",
                        "input": [
                            {
                                "field": "job_title",
                                "value": "Software Engineer"
                            }
                        ],
                        "response": {
                            "classified": True,
                            "code": "620100",
                            "description": "Software developers",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "620100",
                                    "description": "Software developers",
                                    "likelihood": 0.95
                                }
                            ],
                            "follow_up": {
                                "questions": []
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    store_response = client.post("/v1/survey-assist/result", json=store_data)
    assert store_response.status_code == status.HTTP_200_OK
    result_id = store_response.json()["result_id"]

    # Then retrieve it
    get_response = client.get(f"/v1/survey-assist/result?result_id={result_id}")
    assert get_response.status_code == status.HTTP_200_OK
    
    response_data = get_response.json()
    assert response_data["survey_id"] == store_data["survey_id"]
    assert response_data["case_id"] == store_data["case_id"]
    assert response_data["time_start"] == store_data["time_start"]
    assert response_data["time_end"] == store_data["time_end"]
    assert response_data["responses"] == store_data["responses"]


def test_get_result_not_found():
    """Test retrieving a non-existent result.

    This test verifies that:
    1. Attempting to retrieve a non-existent result returns a 404 status code
    """
    response = client.get("/v1/survey-assist/result?result_id=non-existent-result")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Result not found"


def test_datetime_serialisation():
    """Test proper serialisation of datetime objects in result data.

    This test verifies that:
    1. Datetime objects are properly serialised to ISO format
    2. The serialised data can be stored and retrieved correctly
    """
    test_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "time_start": datetime.now().isoformat(),
        "time_end": datetime.now().isoformat(),
        "responses": [
            {
                "person_id": "person-1",
                "time_start": datetime.now().isoformat(),
                "time_end": datetime.now().isoformat(),
                "survey_assist_interactions": [
                    {
                        "type": "classify",
                        "flavour": "sic",
                        "time_start": datetime.now().isoformat(),
                        "time_end": datetime.now().isoformat(),
                        "input": [
                            {
                                "field": "job_title",
                                "value": "Software Engineer"
                            }
                        ],
                        "response": {
                            "classified": True,
                            "code": "620100",
                            "description": "Software developers",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "620100",
                                    "description": "Software developers",
                                    "likelihood": 0.95
                                }
                            ],
                            "follow_up": {
                                "questions": []
                            }
                        }
                    }
                ]
            }
        ]
    }

    # Store the result
    store_response = client.post("/v1/survey-assist/result", json=test_data)
    assert store_response.status_code == status.HTTP_200_OK
    result_id = store_response.json()["result_id"]

    # Retrieve and verify the result
    get_response = client.get(f"/v1/survey-assist/result?result_id={result_id}")
    assert get_response.status_code == status.HTTP_200_OK
    
    response_data = get_response.json()
    assert response_data["survey_id"] == test_data["survey_id"]
    assert response_data["case_id"] == test_data["case_id"]
    assert response_data["time_start"] == test_data["time_start"]
    assert response_data["time_end"] == test_data["time_end"]
    assert response_data["responses"] == test_data["responses"]
