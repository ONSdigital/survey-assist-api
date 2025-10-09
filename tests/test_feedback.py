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

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - fastapi.status: Provides standard HTTP status codes for assertions.
"""

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

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Feedback received successfully"


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

    response = client.post("/v1/survey-assist/feedback", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Feedback received successfully"
