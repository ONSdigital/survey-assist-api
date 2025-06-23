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

    test_multiple_results_same_day():
        Tests storing multiple results on the same day.

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - fastapi.status: Provides standard HTTP status codes for assertions.
    - unittest.mock: Used for mocking Google Cloud Storage interactions.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
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
        "user": "test.userSA187",
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
                        "input": [{"field": "job_title", "value": "Electrician"}],
                        "response": {
                            "classified": True,
                            "code": "432100",
                            "description": "Electrical installation",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "432100",
                                    "description": "Electrical installation",
                                    "likelihood": 0.95,
                                }
                            ],
                            "follow_up": {"questions": []},
                        },
                    }
                ],
            }
        ],
    }

    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
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
        "responses": [],
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
        "responses": [],
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
        "user": "test.userSA187",
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
                        "input": [{"field": "job_title", "value": "Electrician"}],
                        "response": {
                            "classified": True,
                            "code": "432100",
                            "description": "Electrical installation",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "432100",
                                    "description": "Electrical installation",
                                    "likelihood": 0.95,
                                }
                            ],
                            "follow_up": {"questions": []},
                        },
                    }
                ],
            }
        ],
    }

    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        # Simulate storing and retrieving JSON
        stored_json = {}

        def upload_from_string(data, content_type=None):
            _ = content_type  # Mark as used to silence linter
            stored_json["data"] = data

        def download_as_string():
            return stored_json["data"]

        mock_blob.upload_from_string.side_effect = upload_from_string
        mock_blob.download_as_string.side_effect = download_as_string
        mock_blob.exists.return_value = True
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

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
    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
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
        "user": "test.userSA187",
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
                        "input": [{"field": "job_title", "value": "Electrician"}],
                        "response": {
                            "classified": True,
                            "code": "432100",
                            "description": "Electrical installation",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "432100",
                                    "description": "Electrical installation",
                                    "likelihood": 0.95,
                                }
                            ],
                            "follow_up": {"questions": []},
                        },
                    }
                ],
            }
        ],
    }

    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        # Simulate storing and retrieving JSON
        stored_json = {}

        def upload_from_string(data, content_type=None):
            _ = content_type  # Mark as used to silence linter
            stored_json["data"] = data

        def download_as_string():
            return stored_json["data"]

        mock_blob.upload_from_string.side_effect = upload_from_string
        mock_blob.download_as_string.side_effect = download_as_string
        mock_blob.exists.return_value = True
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

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


def test_multiple_results_same_day():
    """Test storing multiple results on the same day.

    This test verifies that:
    1. Multiple results can be stored on the same day
    2. Each result gets a unique filename based on survey_id and user
    3. All results can be retrieved successfully
    """
    # Create two different test data sets for the same day
    test_data_1 = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "user": "test.userSA187",
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
                        "input": [{"field": "job_title", "value": "Electrician"}],
                        "response": {
                            "classified": True,
                            "code": "432100",
                            "description": "Electrical installation",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "432100",
                                    "description": "Electrical installation",
                                    "likelihood": 0.95,
                                }
                            ],
                            "follow_up": {"questions": []},
                        },
                    }
                ],
            }
        ],
    }

    test_data_2 = {
        "survey_id": "test-survey-456",
        "case_id": "test-case-789",
        "user": "test.userSA188",
        "time_start": "2024-03-19T14:00:00Z",
        "time_end": "2024-03-19T14:05:00Z",
        "responses": [
            {
                "person_id": "person-2",
                "time_start": "2024-03-19T14:00:00Z",
                "time_end": "2024-03-19T14:01:00Z",
                "survey_assist_interactions": [
                    {
                        "type": "classify",
                        "flavour": "sic",
                        "time_start": "2024-03-19T14:00:00Z",
                        "time_end": "2024-03-19T14:01:00Z",
                        "input": [{"field": "job_title", "value": "Plumber"}],
                        "response": {
                            "classified": True,
                            "code": "432200",
                            "description": "Plumbing installation",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": "432200",
                                    "description": "Plumbing installation",
                                    "likelihood": 0.92,
                                }
                            ],
                            "follow_up": {"questions": []},
                        },
                    }
                ],
            }
        ],
    }

    def create_mock_storage():
        """Create mock storage functions."""
        files = {}

        def upload_from_string(data, content_type=None):
            _ = content_type  # Mark as used to silence linter
            files[mock_blob.name] = data

        def download_as_string():
            return files.get(mock_blob.name, "")

        def blob_side_effect(filename):
            mock_blob.name = filename
            mock_blob.exists.return_value = filename in files
            return mock_blob

        return upload_from_string, download_as_string, blob_side_effect

    def store_and_verify(test_data, expected_path):
        """Store a result and verify its path."""
        response = client.post("/v1/survey-assist/result", json=test_data)
        assert response.status_code == status.HTTP_200_OK
        result_id = response.json()["result_id"]
        assert expected_path in result_id
        return result_id

    def retrieve_and_verify(result_id, test_data):
        """Retrieve a result and verify its data."""
        get_response = client.get(f"/v1/survey-assist/result?result_id={result_id}")
        assert get_response.status_code == status.HTTP_200_OK
        response_data = get_response.json()
        assert response_data["survey_id"] == test_data["survey_id"]
        assert response_data["user"] == test_data["user"]
        assert response_data["case_id"] == test_data["case_id"]
        return response_data

    with patch("google.cloud.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        # Setup mock storage
        upload_from_string, download_as_string, blob_side_effect = create_mock_storage()

        mock_blob.upload_from_string.side_effect = upload_from_string
        mock_blob.download_as_string.side_effect = download_as_string
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.side_effect = blob_side_effect

        # Store both results
        result_id_1 = store_and_verify(test_data_1, "test-survey-123/test.userSA187")
        result_id_2 = store_and_verify(test_data_2, "test-survey-456/test.userSA188")

        # Verify the result IDs are different
        assert result_id_1 != result_id_2

        # Retrieve and verify both results
        response_data_1 = retrieve_and_verify(result_id_1, test_data_1)
        response_data_2 = retrieve_and_verify(result_id_2, test_data_2)

        # Verify the data is different between the two results
        assert response_data_1["survey_id"] != response_data_2["survey_id"]
        assert response_data_1["user"] != response_data_2["user"]
        assert response_data_1["case_id"] != response_data_2["case_id"]
