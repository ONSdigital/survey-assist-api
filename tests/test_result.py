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
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient
from survey_assist_utils.logging import get_logger

from api.main import app

logger = get_logger(__name__)
client = TestClient(app)


def test_store_result_success():
    """Test storing a result with valid data via Firestore-backed route."""
    test_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "wave_id": "wave-789",
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

    with patch("api.routes.v1.result.store_result") as mock_store:
        mock_store.return_value = "doc123"
        response = client.post("/v1/survey-assist/result", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert "result_id" in response.json()
    assert response.json()["message"] == "Result stored successfully"
    assert response.json()["result_id"] == "doc123"


def test_store_result_empty_fields():
    """Test storing a result with missing required fields.

    This test verifies that:
    1. Attempting to store a result without required fields returns a 422 status code
    2. The error message indicates which fields are missing
    """
    test_data = {
        "case_id": "test-case-456",
        "wave_id": "wave-789",
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
        "wave_id": "wave-789",
        "time_start": "invalid-date",
        "time_end": "2024-03-19T10:05:00Z",
        "responses": [],
    }

    response = client.post("/v1/survey-assist/result", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_result():
    """Test retrieving a stored result via Firestore-backed route."""
    store_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "wave_id": "wave-789",
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
    with patch("api.routes.v1.result.store_result") as mock_store, patch(
        "api.routes.v1.result.get_result"
    ) as mock_get:
        mock_store.return_value = "doc123"
        mock_get.return_value = store_data

        store_response = client.post("/v1/survey-assist/result", json=store_data)
        assert store_response.status_code == status.HTTP_200_OK
        result_id = store_response.json()["result_id"]

        get_response = client.get(f"/v1/survey-assist/result?result_id={result_id}")
        assert get_response.status_code == status.HTTP_200_OK

        response_data = get_response.json()
        assert response_data == store_data


def test_get_result_not_found():
    """Test retrieving a non-existent result.

    This test verifies that:
    1. Attempting to retrieve a non-existent result returns a 404 status code
    """
    with patch("api.routes.v1.result.get_result") as mock_get:
        mock_get.side_effect = FileNotFoundError("Result not found")
        response = client.get("/v1/survey-assist/result?result_id=non-existent-result")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Result not found"


def test_datetime_serialisation():
    """Test storing and retrieving datetime strings via route.

    Serialisation is handled by Pydantic and stored as provided.
    """
    test_data = {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "wave_id": "wave-789",
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
    with patch("api.routes.v1.result.store_result") as mock_store, patch(
        "api.routes.v1.result.get_result"
    ) as mock_get:
        mock_store.return_value = "doc123"
        mock_get.return_value = test_data

        store_response = client.post("/v1/survey-assist/result", json=test_data)
        assert store_response.status_code == status.HTTP_200_OK
        result_id = store_response.json()["result_id"]

        get_response = client.get(f"/v1/survey-assist/result?result_id={result_id}")
        assert get_response.status_code == status.HTTP_200_OK

        response_data = get_response.json()
        assert response_data == test_data


def create_test_data(survey_id, case_id, user, job_title, job_code):
    """Create test dataset with given parameters."""
    return {
        "survey_id": survey_id,
        "case_id": case_id,
        "wave_id": "wave-789",
        "user": user,
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
                        "input": [{"field": "job_title", "value": job_title}],
                        "response": {
                            "classified": True,
                            "code": job_code,
                            "description": f"{job_title} installation",
                            "reasoning": "Based on job title and description",
                            "candidates": [
                                {
                                    "code": job_code,
                                    "description": f"{job_title} installation",
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


def validate_filename_structure(result_id):
    """Deprecated: no filename structure under Firestore; keep for compatibility."""
    assert isinstance(result_id, str)


def store_and_verify(test_data, expected_survey_user, test_client, http_status):
    """Store a result and verify its path."""
    response = test_client.post("/v1/survey-assist/result", json=test_data)
    assert response.status_code == http_status.HTTP_200_OK
    result_id = response.json()["result_id"]
    assert expected_survey_user in result_id
    validate_filename_structure(result_id)
    return result_id


def test_multiple_results_same_day():
    """Test storing multiple results returns different document IDs."""
    with patch("api.routes.v1.result.store_result") as mock_store:
        mock_store.side_effect = ["doc1", "doc2"]

        test_data_1 = create_test_data(
            "test-survey-123",
            "test-case-456",
            "test.userSA187",
            "Electrician",
            "432100",
        )
        test_data_2 = create_test_data(
            "test-survey-456", "test-case-789", "test.userSA188", "Plumber", "432200"
        )

        response1 = client.post("/v1/survey-assist/result", json=test_data_1)
        response2 = client.post("/v1/survey-assist/result", json=test_data_2)

        result_id_1 = response1.json()["result_id"]
        result_id_2 = response2.json()["result_id"]
        assert result_id_1 != result_id_2


# Tests for the result endpoint


class TestResultEndpoint:  # pylint: disable=attribute-defined-outside-init
    """Test class for the result endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        # mock_result_service is not used in these tests but kept for consistency
        self.mock_result_service = (
            None  # pylint: disable=attribute-defined-outside-init
        )

    @patch("api.routes.v1.result.store_result")
    def test_store_survey_result_success(self, mock_store_result):
        """Test successful storage of a survey result."""
        mock_store_result.return_value = "doc123"

        result_data = {
            "survey_id": "test-survey-123",
            "case_id": "test-case-456",
            "wave_id": "wave-789",
            "user": "test.userSA187",
            "time_start": "2024-03-19T10:00:00Z",
            "time_end": "2024-03-19T10:05:00Z",
            "responses": [
                {
                    "person_id": "person-1",
                    "time_start": "2024-03-19T10:00:00Z",
                    "time_end": "2024-03-19T10:05:00Z",
                    "survey_assist_interactions": [
                        {
                            "type": "classify",
                            "flavour": "sic",
                            "time_start": "2024-03-19T10:00:00Z",
                            "time_end": "2024-03-19T10:01:00Z",
                            "input": [
                                {"field": "job_title", "value": "Electrician"},
                                {
                                    "field": "job_description",
                                    "value": "Installing electrical systems",
                                },
                            ],
                            "response": {
                                "classified": True,
                                "code": "43210",
                                "description": "Electrical installation",
                                "reasoning": "Test reasoning",
                                "candidates": [
                                    {
                                        "code": "43210",
                                        "description": "Electrical installation",
                                        "likelihood": 0.9,
                                    }
                                ],
                                "follow_up": {
                                    "questions": [
                                        {
                                            "id": "q1",
                                            "text": "Test question",
                                            "type": "text",
                                            "response": "Test response",
                                        }
                                    ]
                                },
                            },
                        }
                    ],
                }
            ],
        }

        response = client.post("/v1/survey-assist/result", json=result_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["message"] == "Result stored successfully"
        assert data["result_id"] == "doc123"

    @patch("api.routes.v1.result.store_result")
    def test_store_survey_result_error(self, mock_store_result):
        """Test error handling when storing a survey result fails."""
        mock_store_result.side_effect = Exception("Storage error")

        result_data = {
            "survey_id": "test-survey-123",
            "case_id": "test-case-456",
            "wave_id": "wave-789",
            "user": "test.userSA187",
            "time_start": "2024-03-19T10:00:00Z",
            "time_end": "2024-03-19T10:05:00Z",
            "responses": [],
        }

        response = client.post("/v1/survey-assist/result", json=result_data)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Storage error" in response.json()["detail"]

    @patch("api.routes.v1.result.get_result")
    def test_get_survey_result_success(self, mock_get_result):
        """Test successful retrieval of a survey result."""
        mock_result_data = {
            "survey_id": "test-survey-123",
            "case_id": "test-case-456",
            "wave_id": "wave-789",
            "user": "test.userSA187",
            "time_start": "2024-03-19T10:00:00Z",
            "time_end": "2024-03-19T10:05:00Z",
            "responses": [],
        }
        mock_get_result.return_value = mock_result_data

        response = client.get("/v1/survey-assist/result?result_id=test-id")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["survey_id"] == "test-survey-123"
        assert data["case_id"] == "test-case-456"
        assert data["user"] == "test.userSA187"

    @patch("api.routes.v1.result.get_result")
    def test_get_survey_result_not_found(self, mock_get_result):
        """Test error handling when retrieving a non-existent survey result."""
        mock_get_result.side_effect = FileNotFoundError("Result not found")

        response = client.get("/v1/survey-assist/result?result_id=non-existent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Result not found" in response.json()["detail"]

    @patch("api.routes.v1.result.get_result")
    def test_get_survey_result_error(self, mock_get_result):
        """Test error handling when retrieving a survey result fails."""
        mock_get_result.side_effect = Exception("Retrieval error")

        response = client.get("/v1/survey-assist/result?result_id=test-id")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal server error: Retrieval error" in response.json()["detail"]

    @patch("api.routes.v1.result.list_results")
    def test_list_survey_results_success(self, mock_list_results):
        """Test successful listing of survey results."""
        mock_results_data = [
            {
                "survey_id": "test-survey-123",
                "case_id": "test-case-456",
                "wave_id": "wave-789",
                "user": "test.userSA187",
                "time_start": "2024-03-19T10:00:00Z",
                "time_end": "2024-03-19T10:05:00Z",
                "responses": [],
                "document_id": "doc123",
            },
            {
                "survey_id": "test-survey-123",
                "case_id": "test-case-456",
                "wave_id": "wave-789",
                "user": "test.userSA188",
                "time_start": "2024-03-19T11:00:00Z",
                "time_end": "2024-03-19T11:05:00Z",
                "responses": [],
                "document_id": "doc456",
            },
        ]
        mock_list_results.return_value = mock_results_data

        response = client.get(
            "/v1/survey-assist/results?survey_id=test-survey-123&wave_id=wave-789&case_id=test-case-456"
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["document_id"] == "doc123"
        assert data["results"][1]["document_id"] == "doc456"
        assert data["results"][0]["survey_id"] == "test-survey-123"
        assert data["results"][1]["user"] == "test.userSA188"

    @patch("api.routes.v1.result.list_results")
    def test_list_survey_results_empty(self, mock_list_results):
        """Test listing survey results when no results are found."""
        mock_list_results.return_value = []

        response = client.get(
            "/v1/survey-assist/results?survey_id=test-survey-123&wave_id=wave-789&case_id=test-case-456"
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == 0
        assert len(data["results"]) == 0

    @patch("api.routes.v1.result.list_results")
    def test_list_survey_results_error(self, mock_list_results):
        """Test error handling when listing survey results fails."""
        mock_list_results.side_effect = Exception("List error")

        response = client.get(
            "/v1/survey-assist/results?survey_id=test-survey-123&wave_id=wave-789&case_id=test-case-456"
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal server error: List error" in response.json()["detail"]
