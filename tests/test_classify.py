"""This module contains test cases for the classification endpoint of the Survey Assist API.

Functions:
    test_classify_endpoint():
        Tests the classification endpoint with various inputs to ensure correct
        handling of valid and invalid requests.

    test_classify_followup_question():
        Tests that the endpoint returns an appropriate follow-up question when
        additional information is needed for classification.

    test_classify_endpoint_success():
        Tests the structure and content of a successful classification response.

    test_classify_endpoint_invalid_json():
        Tests the endpoint's handling of invalid JSON input.

    test_classify_endpoint_invalid_llm():
        Tests the endpoint's handling of invalid LLM model specifications.

    test_classify_endpoint_invalid_type():
        Tests the endpoint's handling of invalid classification types.

Dependencies:
    - pytest: Used for marking and running test cases.
    - fastapi.testclient.TestClient: Used to simulate HTTP requests to the FastAPI app.
    - fastapi.status: Provides standard HTTP status codes for assertions.
"""

from fastapi import status
from fastapi.testclient import TestClient
from pytest import mark

from api.main import app

client = TestClient(app)


@mark.parametrize(
    "request_data,expected_status_code",
    [
        (
            {
                "llm": "chat-gpt",
                "type": "sic",
                "job_title": "Electrician",
                "job_description": "Installing and maintaining electrical systems",
                "org_description": "Construction company",
            },
            status.HTTP_200_OK,
        ),
        (
            {
                "llm": "chat-gpt",
                "type": "sic",
                "job_title": "",
                "job_description": "",
                "org_description": "test",
            },
            status.HTTP_400_BAD_REQUEST,
        ),
    ],
)
def test_classify_endpoint(request_data, expected_status_code):
    """Test the classification endpoint with various inputs.

    This test verifies the endpoint's handling of both valid and invalid requests.
    It checks:
    1. Successful classification with valid input data.
    2. Error handling for empty job title and description.

    Assertions:
        - The response status code matches the expected value.
    """
    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == expected_status_code


def test_classify_followup_question():
    """Test the follow-up question functionality of the classification endpoint.

    This test verifies that when additional information is needed for classification,
    the endpoint:
    1. Returns a follow-up question.
    2. Sets classified to False.
    3. Provides appropriate candidate codes.
    4. Includes relevant keywords in the follow-up question.

    Assertions:
        - The response status code is 200.
        - classified is False.
        - A follow-up question is present.
        - sic_code and sic_description are None.
        - The follow-up question contains relevant keywords.
    """
    request_data = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Installation Engineer",
        "job_description": "Installing various systems in buildings",
        "org_description": "Construction company",
    }

    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["classified"] is False
    assert data["followup"] is not None
    assert data["sic_code"] is None
    assert data["sic_description"] is None
    assert len(data["sic_candidates"]) > 0
    assert "installation" in data["followup"].lower()
    assert "electrical" in data["followup"].lower()
    assert "plumbing" in data["followup"].lower()


def test_classify_endpoint_success():
    """Test the structure of a successful classification response.

    This test verifies that a successful classification response contains all
    required fields and has the correct structure. It checks:
    1. The response status code is 200.
    2. All required fields are present.
    3. The candidates list contains the expected fields.

    Assertions:
        - The response status code is 200.
        - All required fields are present in the response.
        - The candidates list contains the expected structure.
    """
    response = client.post(
        "/v1/survey-assist/classify",
        json={
            "llm": "chat-gpt",
            "type": "sic",
            "job_title": "Electrician",
            "job_description": "Installing and maintaining electrical systems in buildings",
            "org_description": "Electrical contracting company",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "classified" in data
    assert "sic_code" in data
    assert "sic_description" in data
    assert "sic_candidates" in data
    assert "reasoning" in data
    assert len(data["sic_candidates"]) > 0
    assert "sic_code" in data["sic_candidates"][0]
    assert "sic_descriptive" in data["sic_candidates"][0]
    assert "likelihood" in data["sic_candidates"][0]


def test_classify_endpoint_invalid_json():
    """Test the endpoint's handling of invalid JSON input.

    This test verifies that the endpoint correctly handles invalid JSON input by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate error details.

    Assertions:
        - The response status code is 422.
    """
    response = client.post(
        "/v1/survey-assist/classify",
        json={"invalid": "data"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_classify_endpoint_invalid_llm():
    """Test the endpoint's handling of invalid LLM model specifications.

    This test verifies that the endpoint correctly handles invalid LLM model
    specifications by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate validation error details.

    Assertions:
        - The response status code is 422.
    """
    response = client.post(
        "/v1/survey-assist/classify",
        json={
            "llm": "invalid-model",
            "type": "sic",
            "job_title": "Electrician",
            "job_description": "Installing and maintaining electrical systems",
            "org_description": "Electrical contracting company",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_classify_endpoint_invalid_type():
    """Test the endpoint's handling of invalid classification types.

    This test verifies that the endpoint correctly handles invalid classification
    types by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate validation error details.

    Assertions:
        - The response status code is 422.
    """
    response = client.post(
        "/v1/survey-assist/classify",
        json={
            "llm": "chat-gpt",
            "type": "invalid-type",
            "job_title": "Electrician",
            "job_description": "Installing and maintaining electrical systems",
            "org_description": "Electrical contracting company",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
