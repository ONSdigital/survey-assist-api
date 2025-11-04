"""This module contains test cases for the feedback functionality of the Survey Assist API.

Functions:
    test_store_feedback_success():
        Tests successful feedback storage with valid input data.

    test_store_feedback_empty_fields():
        Tests error handling for missing required fields.

    test_store_feedback_invalid_data():
        Tests error handling for invalid feedback data.

    test_store_feedback_multiple_people():
        Tests storing feedback for multiple people.

    test_store_feedback_different_question_types():
        Tests storing feedback with different question types (radio and text).

    test_get_feedback_success():
        Tests successful retrieval of feedback by ID.

    test_get_feedback_not_found():
        Tests 404 error when feedback not found.

    test_get_feedback_storage_error_valueerror():
        Tests 503 error when storage service returns ValueError.

    test_get_feedback_storage_error_runtimeerror():
        Tests 503 error when storage service returns RuntimeError.

    test_list_feedbacks_success():
        Tests successful listing of feedbacks by survey_id and wave_id.

    test_list_feedbacks_with_case_id():
        Tests successful listing of feedbacks by survey_id, wave_id, and case_id.

    test_list_feedbacks_empty():
        Tests listing feedbacks when no results are found.

    test_list_feedbacks_storage_error_valueerror():
        Tests 503 error when listing feedbacks and storage service returns ValueError.

    test_list_feedbacks_storage_error_runtimeerror():
        Tests 503 error when listing feedbacks and storage service returns RuntimeError.

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - fastapi.status: Provides standard HTTP status codes for assertions.
"""

from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient
from survey_assist_utils.logging import get_logger

from api.main import app

logger = get_logger(__name__)
client = TestClient(app)


def test_store_feedback_success():
    """Test storing feedback with valid data.

    This test verifies that:
    1. A valid feedback request can be stored successfully
    2. The response contains the correct success message
    3. The endpoint processes the feedback data correctly
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Very satisfied",
                "response_name": "satisfaction_question",
                "response_options": [
                    "Very satisfied",
                    "Satisfied",
                    "Neutral",
                    "Dissatisfied",
                    "Very dissatisfied",
                ],
            },
            {
                "response": "The survey was easy to complete and helpful.",
                "response_name": "comments_question",
                "response_options": None,
            },
        ],
    }

    with patch("api.services.feedback_service.get_firestore_client") as mock_db:
        mock_db.return_value.collection.return_value.document.return_value.id = "fb123"
        response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Feedback received successfully"
    assert response.json()["feedback_id"] == "fb123"


def test_store_feedback_empty_fields():
    """Test storing feedback with missing required fields.

    This test verifies that:
    1. Attempting to store feedback without required fields returns a 422 status code
    2. The error message indicates which fields are missing
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response_name": "test_question",
                # Missing required "response" field
            }
        ],
    }

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_feedback_invalid_data():
    """Test storing feedback with invalid data structure.

    This test verifies that:
    1. Attempting to store feedback with invalid data returns a 422 status code
    2. The error message indicates which fields are invalid
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Test answer",
                "response_name": "test_question",
                "response_options": "invalid_options_format",  # Should be array
            }
        ],
    }

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_feedback_multiple_questions():
    """Test storing feedback with multiple questions.

    This test verifies that:
    1. Feedback can be stored with multiple questions in a single request
    2. Each question's feedback is processed correctly
    3. The response indicates successful processing
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Very satisfied",
                "response_name": "satisfaction_question",
                "response_options": [
                    "Very satisfied",
                    "Satisfied",
                    "Neutral",
                    "Dissatisfied",
                    "Very dissatisfied",
                ],
            },
            {
                "response": "Good",
                "response_name": "clarity_question",
                "response_options": ["Excellent", "Good", "Fair", "Poor"],
            },
            {
                "response": "Could use more examples in the job description section.",
                "response_name": "suggestions_question",
                "response_options": None,
            },
        ],
    }

    with patch("api.services.feedback_service.get_firestore_client") as mock_db:
        mock_db.return_value.collection.return_value.document.return_value.id = "fb456"
        response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Feedback received successfully"


def test_store_feedback_different_question_types():
    """Test storing feedback with different question types.

    This test verifies that:
    1. Radio questions (with options) are handled correctly
    2. Text questions (without options) are handled correctly
    3. Mixed question types in the same request work properly
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Very satisfied",
                "response_name": "satisfaction_question",
                "response_options": [
                    "Very satisfied",
                    "Satisfied",
                    "Neutral",
                    "Dissatisfied",
                    "Very dissatisfied",
                ],
            },
            {
                "response": "The survey was easy to complete and helpful.",
                "response_name": "comments_question",
                "response_options": None,
            },
            {
                "response": "Good",
                "response_name": "clarity_question",
                "response_options": ["Excellent", "Good", "Fair", "Poor"],
            },
        ],
    }

    with patch("api.services.feedback_service.get_firestore_client") as mock_db:
        mock_db.return_value.collection.return_value.document.return_value.id = "fb789"
        response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Feedback received successfully"


def test_store_feedback_missing_case_id():
    """Test storing feedback without case_id.

    This test verifies that:
    1. Attempting to store feedback without case_id returns a 422 status code
    2. The error message indicates the missing field
    """
    test_data = {
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Test answer",
                "response_name": "test_question",
                "response_options": None,
            }
        ],
    }

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_feedback_missing_person_id():
    """Test storing feedback without person_id.

    This test verifies that:
    1. Attempting to store feedback without person_id returns a 422 status code
    2. The error message indicates the missing field
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Test answer",
                "response_name": "test_question",
                "response_options": None,
            }
        ],
    }

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_feedback_missing_survey_id():
    """Test storing feedback without survey_id.

    This test verifies that:
    1. Attempting to store feedback without survey_id returns a 422 status code
    2. The error message indicates the missing field
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Test answer",
                "response_name": "test_question",
                "response_options": None,
            }
        ],
    }

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_feedback_missing_wave_id():
    """Test storing feedback without wave_id.

    This test verifies that:
    1. Attempting to store feedback without wave_id returns a 422 status code
    2. The error message indicates the missing field
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "questions": [
            {
                "response": "Test answer",
                "response_name": "test_question",
                "response_options": None,
            }
        ],
    }

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_store_feedback_empty_questions_array():
    """Test storing feedback with empty questions array.

    This test verifies that:
    1. An empty questions array is handled gracefully
    2. The response indicates successful processing
    """
    test_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [],
    }

    with patch("api.services.feedback_service.get_firestore_client") as mock_db:
        mock_db.return_value.collection.return_value.document.return_value.id = (
            "fb_empty"
        )
        response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Feedback received successfully"


def test_get_feedback_success():
    """Test retrieving a stored feedback by ID.

    This test verifies that:
    1. A valid feedback ID can be retrieved successfully
    2. The response contains the correct feedback data
    """
    test_feedback_data = {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
            {
                "response": "Very satisfied",
                "response_name": "satisfaction_question",
                "response_options": [
                    "Very satisfied",
                    "Satisfied",
                    "Neutral",
                    "Dissatisfied",
                    "Very dissatisfied",
                ],
            }
        ],
    }

    with patch("api.routes.v1.feedback.get_feedback") as mock_get:
        mock_get.return_value = test_feedback_data
        response = client.get("/v1/survey-assist/feedback?feedback_id=fb123")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["case_id"] == "0710-25AA-XXXX-YYYY"
        assert response.json()["survey_id"] == "survey_123"


def test_get_feedback_not_found():
    """Test retrieving a non-existent feedback.

    This test verifies that:
    1. Attempting to retrieve a non-existent feedback returns a 404 status code
    """
    with patch("api.routes.v1.feedback.get_feedback") as mock_get:
        mock_get.side_effect = FileNotFoundError("Feedback not found")
        response = client.get("/v1/survey-assist/feedback?feedback_id=non-existent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Feedback not found"


def test_get_feedback_storage_error_valueerror():
    """Test retrieving feedback when storage service returns ValueError.

    This test verifies that:
    1. A ValueError from storage service returns a 503 status code
    """
    with patch("api.routes.v1.feedback.get_feedback") as mock_get:
        mock_get.side_effect = ValueError("Storage service unavailable")
        response = client.get("/v1/survey-assist/feedback?feedback_id=fb123")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Storage service unavailable" in response.json()["detail"]


def test_get_feedback_storage_error_runtimeerror():
    """Test retrieving feedback when storage service returns RuntimeError.

    This test verifies that:
    1. A RuntimeError from storage service returns a 503 status code
    """
    with patch("api.routes.v1.feedback.get_feedback") as mock_get:
        mock_get.side_effect = RuntimeError("Storage service error")
        response = client.get("/v1/survey-assist/feedback?feedback_id=fb123")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Storage service error" in response.json()["detail"]


def test_list_feedbacks_success():
    """Test listing feedbacks by survey_id and wave_id.

    This test verifies that:
    1. Feedbacks can be retrieved by survey_id and wave_id
    2. The response contains a list with document_id field included
    """
    expected_count = 2
    mock_feedbacks_data = [
        {
            "case_id": "0710-25AA-XXXX-YYYY",
            "person_id": "000001_01",
            "survey_id": "survey_123",
            "wave_id": "wave_456",
            "questions": [],
            "document_id": "fb123",
        },
        {
            "case_id": "0710-25AA-XXXX-YYYY",
            "person_id": "000002_01",
            "survey_id": "survey_123",
            "wave_id": "wave_456",
            "questions": [],
            "document_id": "fb456",
        },
    ]

    with patch("api.routes.v1.feedback.list_feedbacks") as mock_list:
        mock_list.return_value = mock_feedbacks_data
        response = client.get(
            "/v1/survey-assist/feedbacks?survey_id=survey_123&wave_id=wave_456"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == expected_count
        assert len(data["results"]) == expected_count
        assert data["results"][0]["document_id"] == "fb123"
        assert data["results"][1]["document_id"] == "fb456"


def test_list_feedbacks_with_case_id():
    """Test listing feedbacks by survey_id, wave_id, and case_id.

    This test verifies that:
    1. Feedbacks can be retrieved by survey_id, wave_id, and case_id
    2. The response contains a list with document_id field included
    """
    expected_count = 1
    mock_feedbacks_data = [
        {
            "case_id": "0710-25AA-XXXX-YYYY",
            "person_id": "000001_01",
            "survey_id": "survey_123",
            "wave_id": "wave_456",
            "questions": [],
            "document_id": "fb123",
        }
    ]

    with patch("api.routes.v1.feedback.list_feedbacks") as mock_list:
        mock_list.return_value = mock_feedbacks_data
        response = client.get(
            "/v1/survey-assist/feedbacks?"
            "survey_id=survey_123&wave_id=wave_456&case_id=0710-25AA-XXXX-YYYY"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == expected_count
        assert len(data["results"]) == expected_count
        assert data["results"][0]["document_id"] == "fb123"
        assert data["results"][0]["case_id"] == "0710-25AA-XXXX-YYYY"


def test_list_feedbacks_empty():
    """Test listing feedbacks when no feedbacks are found.

    This test verifies that:
    1. An empty list is returned when no feedbacks match the criteria
    """
    with patch("api.routes.v1.feedback.list_feedbacks") as mock_list:
        mock_list.return_value = []
        response = client.get(
            "/v1/survey-assist/feedbacks?survey_id=survey_123&wave_id=wave_456"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 0
        assert len(data["results"]) == 0


def test_list_feedbacks_storage_error_valueerror():
    """Test listing feedbacks when storage service returns ValueError.

    This test verifies that:
    1. A ValueError from storage service returns a 503 status code
    """
    with patch("api.routes.v1.feedback.list_feedbacks") as mock_list:
        mock_list.side_effect = ValueError("Storage service unavailable")
        response = client.get(
            "/v1/survey-assist/feedbacks?survey_id=survey_123&wave_id=wave_456"
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Storage service unavailable" in response.json()["detail"]


def test_list_feedbacks_storage_error_runtimeerror():
    """Test listing feedbacks when storage service returns RuntimeError.

    This test verifies that:
    1. A RuntimeError from storage service returns a 503 status code
    """
    with patch("api.routes.v1.feedback.list_feedbacks") as mock_list:
        mock_list.side_effect = RuntimeError("Storage service error")
        response = client.get(
            "/v1/survey-assist/feedbacks?survey_id=survey_123&wave_id=wave_456"
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Storage service error" in response.json()["detail"]
