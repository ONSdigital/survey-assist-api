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

import logging
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from pytest import mark

from api.main import app

logger = logging.getLogger(__name__)
client = TestClient(app)

# Constants for test values
EXPECTED_LIKELIHOOD = 0.9
EXPECTED_SIC_CODE = "43210"
EXPECTED_SIC_DESCRIPTION = "Electrical installation"


class TestClassifyEndpoint:
    """Test class for the classification endpoint."""

    def __init__(self):
        """Initialise test class attributes."""
        self.mock_auth = None
        self.mock_llm = None
        self.mock_vector_store = None
        self.mock_vertexai = None

    @patch("api.routes.v1.classify.VertexAI")
    @patch("api.routes.v1.classify.SICVectorStoreClient")
    @patch("api.routes.v1.classify.ClassificationLLM")
    @patch("google.auth.default")
    def setup_method(self, mock_auth, mock_llm, mock_vector_store, mock_vertexai):
        """Set up test fixtures."""
        self.mock_auth = mock_auth
        self.mock_llm = mock_llm
        self.mock_vector_store = mock_vector_store
        self.mock_vertexai = mock_vertexai

        self.mock_auth.return_value = (MagicMock(), "test-project")
        self.mock_vertexai.return_value = MagicMock()
        self.mock_vector_store.return_value.search = AsyncMock(
            return_value=[
                {
                    "code": EXPECTED_SIC_CODE,
                    "title": EXPECTED_SIC_DESCRIPTION,
                    "distance": 0.05,
                }
            ]
        )
        mock_llm_instance = MagicMock()
        mock_llm_instance.sa_rag_sic_code.return_value = (
            MagicMock(
                classified=True,
                followup=None,
                class_code=EXPECTED_SIC_CODE,
                class_descriptive=EXPECTED_SIC_DESCRIPTION,
                reasoning="Mocked reasoning",
                alt_candidates=[],
            ),
            None,
            None,
        )
        self.mock_llm.return_value = mock_llm_instance

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
    def test_classify_endpoint(self, request_data, expected_status_code):
        """Test the classification endpoint with various inputs.

        This test verifies the endpoint's handling of both valid and invalid requests.
        It checks:
        1. Successful classification with valid input data.
        2. Error handling for empty job title and description.

        Assertions:
            - The response status code matches the expected value.
        """
        logger.info("Testing classify endpoint with data: %s", request_data)
        response = client.post("/v1/survey-assist/classify", json=request_data)
        assert response.status_code == expected_status_code
        logger.info("Received response with status code: %d", response.status_code)


@patch("api.routes.v1.classify.VertexAI")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.routes.v1.classify.ClassificationLLM")
@patch("google.auth.default")
def test_classify_followup_question(
    mock_auth, mock_llm, mock_vector_store, mock_vertexai
):
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
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vertexai.return_value = MagicMock()
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )
    mock_llm_instance = MagicMock()
    mock_llm_instance.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=False,
            followup="Please specify if this is electrical or plumbing installation.",
            class_code=None,
            class_descriptive=None,
            reasoning="Mocked reasoning",
            alt_candidates=[
                MagicMock(
                    class_code=EXPECTED_SIC_CODE,
                    class_descriptive=EXPECTED_SIC_DESCRIPTION,
                    likelihood=0.8,
                )
            ],
        ),
        None,
        None,
    )
    mock_llm.return_value = mock_llm_instance

    request_data = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Installation Engineer",
        "job_description": "Installing various systems in buildings",
        "org_description": "Construction company",
    }

    logger.info("Testing follow-up question with data: %s", request_data)
    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    logger.info("Received response data: %s", data)
    assert data["classified"] is False
    assert data["followup"] is not None
    assert data["sic_code"] is None
    assert data["sic_description"] is None
    assert len(data["sic_candidates"]) > 0
    assert "installation" in data["followup"].lower()
    assert "electrical" in data["followup"].lower()
    assert "plumbing" in data["followup"].lower()


@patch("api.routes.v1.classify.VertexAI")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.routes.v1.classify.ClassificationLLM")
@patch("google.auth.default")
def test_classify_endpoint_success(
    mock_auth, mock_llm, mock_vector_store, mock_vertexai
):
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
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vertexai.return_value = MagicMock()
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )
    mock_llm_instance = MagicMock()
    mock_llm_instance.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=True,
            followup=None,
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            reasoning="Mocked reasoning",
            alt_candidates=[
                MagicMock(
                    class_code=EXPECTED_SIC_CODE,
                    class_descriptive=EXPECTED_SIC_DESCRIPTION,
                    likelihood=EXPECTED_LIKELIHOOD,
                )
            ],
        ),
        None,
        None,
    )
    mock_llm.return_value = mock_llm_instance

    request_data = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems in buildings",
        "org_description": "Electrical contracting company",
    }

    logger.info("Testing successful classification with data: %s", request_data)
    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    logger.info("Received response data: %s", data)
    assert data["classified"] is True
    assert data["followup"] is None
    assert data["sic_code"] == EXPECTED_SIC_CODE
    assert data["sic_description"] == EXPECTED_SIC_DESCRIPTION
    assert len(data["sic_candidates"]) == 1
    assert data["sic_candidates"][0]["sic_code"] == EXPECTED_SIC_CODE
    assert data["sic_candidates"][0]["sic_descriptive"] == EXPECTED_SIC_DESCRIPTION
    assert data["sic_candidates"][0]["likelihood"] == EXPECTED_LIKELIHOOD


@patch("api.routes.v1.classify.VertexAI")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.routes.v1.classify.ClassificationLLM")
@patch("google.auth.default")
def test_classify_endpoint_invalid_json(
    mock_auth, mock_llm, mock_vector_store, mock_vertexai
):
    """Test the endpoint's handling of invalid JSON input.

    This test verifies that the endpoint correctly handles invalid JSON input by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate error details.

    Assertions:
        - The response status code is 422.
    """
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vertexai.return_value = MagicMock()
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )
    mock_llm_instance = MagicMock()
    mock_llm_instance.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=True,
            followup=None,
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            reasoning="Mocked reasoning",
            alt_candidates=[],
        ),
        None,
        None,
    )
    mock_llm.return_value = mock_llm_instance

    request_data = {"invalid": "data"}
    logger.info("Testing invalid JSON with data: %s", request_data)
    response = client.post(
        "/v1/survey-assist/classify",
        json=request_data,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("api.routes.v1.classify.VertexAI")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.routes.v1.classify.ClassificationLLM")
@patch("google.auth.default")
def test_classify_endpoint_invalid_llm(
    mock_auth, mock_llm, mock_vector_store, mock_vertexai
):
    """Test the endpoint's handling of invalid LLM model specifications.

    This test verifies that the endpoint correctly handles invalid LLM model
    specifications by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate validation error details.

    Assertions:
        - The response status code is 422.
    """
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vertexai.return_value = MagicMock()
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )
    mock_llm_instance = MagicMock()
    mock_llm_instance.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=True,
            followup=None,
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            reasoning="Mocked reasoning",
            alt_candidates=[],
        ),
        None,
        None,
    )
    mock_llm.return_value = mock_llm_instance

    request_data = {
        "llm": "invalid-model",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems",
        "org_description": "Electrical contracting company",
    }

    logger.info("Testing invalid LLM model with data: %s", request_data)
    response = client.post(
        "/v1/survey-assist/classify",
        json=request_data,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("api.routes.v1.classify.VertexAI")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.routes.v1.classify.ClassificationLLM")
@patch("google.auth.default")
def test_classify_endpoint_invalid_type(
    mock_auth, mock_llm, mock_vector_store, mock_vertexai
):
    """Test the endpoint's handling of invalid classification types.

    This test verifies that the endpoint correctly handles invalid classification
    types by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate validation error details.

    Assertions:
        - The response status code is 422.
    """
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vertexai.return_value = MagicMock()
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )
    mock_llm_instance = MagicMock()
    mock_llm_instance.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=True,
            followup=None,
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            reasoning="Mocked reasoning",
            alt_candidates=[],
        ),
        None,
        None,
    )
    mock_llm.return_value = mock_llm_instance

    request_data = {
        "llm": "chat-gpt",
        "type": "invalid-type",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems",
        "org_description": "Electrical contracting company",
    }

    logger.info("Testing invalid classification type with data: %s", request_data)
    response = client.post(
        "/v1/survey-assist/classify",
        json=request_data,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
