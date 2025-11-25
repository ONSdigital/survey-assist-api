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

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from survey_assist_utils.logging import get_logger

from api.main import app

logger = get_logger(__name__)
client = TestClient(app)

# Constants for test values
EXPECTED_LIKELIHOOD = 0.9
EXPECTED_SIC_CODE = "43210"
EXPECTED_SIC_DESCRIPTION = "Electrical installation"
EXPECTED_SOC_CODE = "9111"
EXPECTED_SOC_DESCRIPTION = "Farm workers"
EXPECTED_COMBINED_RESULTS_COUNT = 2  # SIC + SOC results


class TestClassifyEndpoint:
    """Test class for the classification endpoint."""

    def __init__(self):
        """Initialise test class attributes."""
        self.mock_auth = None
        self.mock_llm = None
        self.mock_vector_store = None
        self.mock_vertexai = None
        self.mock_rephrase_client = None

    @patch("api.routes.v1.classify.SICRephraseClient")
    @patch("api.routes.v1.classify.SICVectorStoreClient")
    @patch("api.main.app.state.gemini_llm")
    @patch("google.auth.default")
    def setup_method(
        self, mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
    ):
        """Set up test fixtures."""
        self.mock_auth = mock_auth
        self.mock_llm = mock_llm
        self.mock_vector_store = mock_vector_store
        self.mock_rephrase_client = mock_rephrase_client

        self.mock_auth.return_value = (MagicMock(), "test-project")
        self.mock_vector_store.return_value.search = AsyncMock(
            return_value=[
                {
                    "code": EXPECTED_SIC_CODE,
                    "title": EXPECTED_SIC_DESCRIPTION,
                    "distance": 0.05,
                }
            ]
        )

        # Mock the rephrase client
        mock_rephrase_instance = MagicMock()
        mock_rephrase_instance.process_classification_response.return_value = {
            "classified": True,
            "followup": None,
            "sic_code": EXPECTED_SIC_CODE,
            "sic_description": EXPECTED_SIC_DESCRIPTION,
            "sic_candidates": [],
            "reasoning": "Mocked reasoning",
            "prompt_used": None,
        }
        mock_rephrase_instance.get_rephrased_count.return_value = 0
        self.mock_rephrase_client.return_value = mock_rephrase_instance

        self.mock_llm.sa_rag_sic_code = AsyncMock(
            return_value=(
                MagicMock(
                    classified=True,
                    codable=True,
                    followup=None,
                    class_code=EXPECTED_SIC_CODE,
                    class_descriptive=EXPECTED_SIC_DESCRIPTION,
                    reasoning="Mocked reasoning",
                    alt_candidates=[],
                ),
                None,
                None,
            )
        )

    @pytest.mark.parametrize(
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
        logger.info("Testing classify endpoint with data", request_data=request_data)
        response = client.post("/v1/survey-assist/classify", json=request_data)
        assert response.status_code == expected_status_code
        logger.info(
            "Received response with status code", status_code=response.status_code
        )


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_followup_question(  # pylint: disable=too-many-locals
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
):
    """Test the follow-up question functionality of the classification endpoint.

    This test verifies that when additional information is needed for classification,
    the endpoint:
    1. Returns a follow-up question.
    2. Sets classified to False.
    3. Provides appropriate candidate codes.
    4. Includes relevant keywords in the follow-up question.
    5. Passes all alternative candidates to formulate_open_question (not just the first).

    Assertions:
        - The response status code is 200.
        - classified is False.
        - A follow-up question is present.
        - sic_code and sic_description are None.
        - The follow-up question contains relevant keywords.
        - All candidates from alt_candidates are passed to formulate_open_question.
    """
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_instance.process_classification_response.return_value = {
        "classified": False,
        "followup": "Please specify if this is electrical or plumbing installation.",
        "sic_code": None,
        "sic_description": None,
        "sic_candidates": [
            {
                "sic_code": EXPECTED_SIC_CODE,
                "sic_descriptive": EXPECTED_SIC_DESCRIPTION,
                "likelihood": 0.8,
            }
        ],
        "reasoning": "Mocked reasoning",
        "prompt_used": None,
    }
    mock_rephrase_instance.get_rephrased_count.return_value = 0
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock the new two-step process - unambiguous returns no match, then open question
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = False
    mock_unambiguous_response.class_code = None
    mock_unambiguous_response.class_descriptive = None
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    # Create multiple candidates to verify all are passed to formulate_open_question
    candidate1 = MagicMock(
        class_code=EXPECTED_SIC_CODE,
        class_descriptive=EXPECTED_SIC_DESCRIPTION,
        likelihood=0.8,
    )
    candidate2 = MagicMock(
        class_code="43320",
        class_descriptive="Plumbing installation",
        likelihood=0.75,
    )
    candidate3 = MagicMock(
        class_code="43330",
        class_descriptive="Other building installation",
        likelihood=0.65,
    )
    mock_unambiguous_response.alt_candidates = [candidate1, candidate2, candidate3]
    expected_candidates_count = len(mock_unambiguous_response.alt_candidates)

    mock_open_question_response = MagicMock()
    mock_open_question_response.followup = (
        "Please specify if this is electrical or plumbing installation."
    )

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )
    mock_llm.formulate_open_question = AsyncMock(
        return_value=(mock_open_question_response, None)
    )
    request_data = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Installation Engineer",
        "job_description": "Installing various systems in buildings",
        "org_description": "Construction company",
        "prompt_version": "v3",
    }

    logger.info("Testing follow-up question with data", request_data=request_data)
    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    logger.info("Received response data", data=data)
    result = data["results"][0]
    assert result["classified"] is False
    assert result["followup"] is not None
    assert result["code"] is None
    assert result["description"] is None
    assert len(result["candidates"]) > 0
    assert "installation" in result["followup"].lower()
    assert "electrical" in result["followup"].lower()
    assert "plumbing" in result["followup"].lower()

    # Verify that all candidates were passed to formulate_open_question
    assert mock_llm.formulate_open_question.called
    call_args = mock_llm.formulate_open_question.call_args
    assert call_args is not None
    llm_output = call_args.kwargs.get("llm_output")
    assert llm_output == mock_unambiguous_response.alt_candidates, (
        "formulate_open_question should receive the full list of candidates, "
        f"not just the first one. Expected {len(mock_unambiguous_response.alt_candidates)} "
        f"candidates, got {len(llm_output) if llm_output else 0}"
    )
    assert (
        len(llm_output) == expected_candidates_count
    ), f"Expected {expected_candidates_count} candidates to be passed, got {len(llm_output)}"


@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("api.main.app.state.sic_rephrase_client")
@patch("google.auth.default")
def test_classify_endpoint_success(
    mock_auth, mock_rephrase_client, mock_llm, mock_vector_store
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
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_client.get_rephrased_description.return_value = (
        EXPECTED_SIC_DESCRIPTION
    )

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = EXPECTED_SIC_CODE
    mock_unambiguous_response.class_descriptive = EXPECTED_SIC_DESCRIPTION
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            likelihood=EXPECTED_LIKELIHOOD,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems in buildings",
        "org_description": "Electrical contracting company",
        "prompt_version": "v3",
    }

    logger.info(
        "Testing successful classification with data", request_data=request_data
    )
    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    logger.info("Received response data", data=data)
    result = data["results"][0]
    assert result["classified"] is True
    assert result["followup"] is None
    assert result["code"] == EXPECTED_SIC_CODE
    assert result["description"] == EXPECTED_SIC_DESCRIPTION
    assert len(result["candidates"]) > 0
    assert result["candidates"][0]["code"] == EXPECTED_SIC_CODE
    assert result["candidates"][0]["descriptive"] == EXPECTED_SIC_DESCRIPTION
    assert result["candidates"][0]["likelihood"] == EXPECTED_LIKELIHOOD


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_endpoint_invalid_json(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
):
    """Test the endpoint's handling of invalid JSON input.

    This test verifies that the endpoint correctly handles invalid JSON input by:
    1. Returning a 422 Unprocessable Entity status code.
    2. Providing appropriate error details.

    Assertions:
        - The response status code is 422.
    """
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = EXPECTED_SIC_CODE
    mock_unambiguous_response.class_descriptive = EXPECTED_SIC_DESCRIPTION
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            likelihood=EXPECTED_LIKELIHOOD,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {"invalid": "data"}
    logger.info("Testing invalid JSON with data", request_data=request_data)
    response = client.post(
        "/v1/survey-assist/classify",
        json=request_data,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_endpoint_invalid_llm(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
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
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = EXPECTED_SIC_CODE
    mock_unambiguous_response.class_descriptive = EXPECTED_SIC_DESCRIPTION
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            likelihood=EXPECTED_LIKELIHOOD,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "invalid-model",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems",
        "org_description": "Electrical contracting company",
    }

    logger.info("Testing invalid LLM model with data", request_data=request_data)
    response = client.post(
        "/v1/survey-assist/classify",
        json=request_data,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_endpoint_invalid_type(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
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
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = EXPECTED_SIC_CODE
    mock_unambiguous_response.class_descriptive = EXPECTED_SIC_DESCRIPTION
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            likelihood=EXPECTED_LIKELIHOOD,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "chat-gpt",
        "type": "invalid-type",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems",
        "org_description": "Electrical contracting company",
    }

    logger.info(
        "Testing invalid classification type with data", request_data=request_data
    )
    response = client.post(
        "/v1/survey-assist/classify",
        json=request_data,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("api.main.app.state.sic_rephrase_client")
@patch("google.auth.default")
def test_classify_endpoint_rephrasing_enabled(
    mock_auth, mock_rephrase_client, mock_llm, mock_vector_store
):
    """Test that rephrasing is enabled when explicitly set to True."""
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": "01110",
                "title": (
                    "Growing of cereals (except rice), leguminous crops and oil seeds"
                ),
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client with rephrased descriptions
    mock_rephrase_client.get_rephrased_description.return_value = "Crop growing"

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = "01110"
    mock_unambiguous_response.class_descriptive = (
        "Growing of cereals (except rice), leguminous crops and oil seeds"
    )
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code="01110",
            class_descriptive="Growing of cereals (except rice), leguminous crops and oil seeds",
            likelihood=0.9,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "gemini",
        "type": "sic",
        "job_title": "Farmer",
        "job_description": "Growing cereals and crops",
        "org_description": "Agricultural farm",
        "options": {"sic": {"rephrased": True}},
        "prompt_version": "v3",
    }

    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["requested_type"] == "sic"
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["type"] == "sic"
    assert result["classified"] is True
    assert result["code"] == "01110"
    # Main description stays original
    assert (
        result["description"]
        == "Growing of cereals (except rice), leguminous crops and oil seeds"
    )
    assert len(result["candidates"]) > 0
    # Check that candidates have rephrased descriptions
    for candidate in result["candidates"]:
        if candidate["code"] == "01110":
            assert candidate["descriptive"] == "Crop growing"


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_endpoint_rephrasing_disabled(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
):
    """Test that rephrasing is disabled when explicitly set to False."""
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": "01110",
                "title": (
                    "Growing of cereals (except rice), leguminous crops and oil seeds"
                ),
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = "01110"
    mock_unambiguous_response.class_descriptive = (
        "Growing of cereals (except rice), leguminous crops and oil seeds"
    )
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code="01110",
            class_descriptive="Growing of cereals (except rice), leguminous crops and oil seeds",
            likelihood=0.9,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "gemini",
        "type": "sic",
        "job_title": "Farmer",
        "job_description": "Growing cereals and crops",
        "org_description": "Agricultural farm",
        "options": {"sic": {"rephrased": False}},
        "prompt_version": "v3",
    }

    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["requested_type"] == "sic"
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["type"] == "sic"
    assert result["classified"] is True
    assert result["code"] == "01110"
    # Main description stays original
    assert (
        result["description"]
        == "Growing of cereals (except rice), leguminous crops and oil seeds"
    )
    assert len(result["candidates"]) > 0
    # Check that candidates also have original descriptions
    for candidate in result["candidates"]:
        if candidate["code"] == "01110":
            assert (
                candidate["descriptive"]
                == "Growing of cereals (except rice), leguminous crops and oil seeds"
            )


@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("api.main.app.state.sic_rephrase_client")
@patch("google.auth.default")
def test_classify_endpoint_rephrasing_default(
    mock_auth, mock_rephrase_client, mock_llm, mock_vector_store
):
    """Test that rephrasing defaults to True when no options provided."""
    mock_auth.return_value = (MagicMock(), "test-project")
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": "01110",
                "title": (
                    "Growing of cereals (except rice), leguminous crops and oil seeds"
                ),
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client with rephrased descriptions
    mock_rephrase_client.get_rephrased_description.return_value = "Crop growing"

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = "01110"
    mock_unambiguous_response.class_descriptive = (
        "Growing of cereals (except rice), leguminous crops and oil seeds"
    )
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code="01110",
            class_descriptive="Growing of cereals (except rice), leguminous crops and oil seeds",
            likelihood=0.9,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "gemini",
        "type": "sic",
        "job_title": "Farmer",
        "job_description": "Growing cereals and crops",
        "org_description": "Agricultural farm",
        "prompt_version": "v3",
    }

    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["requested_type"] == "sic"
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert result["type"] == "sic"
    assert result["classified"] is True
    assert result["code"] == "01110"
    # Main description stays original (default behaviour)
    assert (
        result["description"]
        == "Growing of cereals (except rice), leguminous crops and oil seeds"
    )
    assert len(result["candidates"]) > 0
    # Check that candidates have rephrased descriptions
    for candidate in result["candidates"]:
        if candidate["code"] == "01110":
            assert candidate["descriptive"] == "Crop growing"


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_endpoint_rephrasing_options_validation(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
):
    """Test that invalid options are properly validated."""
    # Mock auth
    mock_auth.return_value = (MagicMock(), "test-project")

    # Mock vector store
    mock_vector_store.return_value.search = AsyncMock(return_value=[])

    # Mock rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock LLM (not needed for validation test but required)
    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = EXPECTED_SIC_CODE
    mock_unambiguous_response.class_descriptive = EXPECTED_SIC_DESCRIPTION
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            likelihood=EXPECTED_LIKELIHOOD,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    request_data = {
        "llm": "gemini",
        "type": "sic",
        "job_title": "Farmer",
        "job_description": "Growing cereals and crops",
        "org_description": "Agricultural farm",
        "options": {"sic": {"rephrased": "not_a_boolean"}},  # Invalid type
    }

    response = client.post("/v1/survey-assist/classify", json=request_data)
    assert (
        response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    )  # Validation error


@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_classify_endpoint_meta_field_exclusion(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
):
    """Test that the meta field is excluded when options are not provided."""
    # Mock auth
    mock_auth.return_value = (MagicMock(), "test-project")

    # Mock vector store
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": EXPECTED_SIC_CODE,
                "title": EXPECTED_SIC_DESCRIPTION,
                "distance": 0.05,
            }
        ]
    )

    # Mock the rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_instance.process_classification_response.return_value = {
        "classified": True,
        "followup": None,
        "sic_code": EXPECTED_SIC_CODE,
        "sic_description": EXPECTED_SIC_DESCRIPTION,
        "sic_candidates": [
            {
                "sic_code": EXPECTED_SIC_CODE,
                "sic_descriptive": EXPECTED_SIC_DESCRIPTION,
                "likelihood": EXPECTED_LIKELIHOOD,
            }
        ],
        "reasoning": "Mocked reasoning",
        "prompt_used": None,
    }
    mock_rephrase_instance.get_rephrased_count.return_value = 0
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Mock the new two-step process
    mock_unambiguous_response = MagicMock()
    mock_unambiguous_response.codable = True
    mock_unambiguous_response.class_code = EXPECTED_SIC_CODE
    mock_unambiguous_response.class_descriptive = EXPECTED_SIC_DESCRIPTION
    mock_unambiguous_response.reasoning = "Mocked reasoning"
    mock_unambiguous_response.alt_candidates = [
        MagicMock(
            class_code=EXPECTED_SIC_CODE,
            class_descriptive=EXPECTED_SIC_DESCRIPTION,
            likelihood=EXPECTED_LIKELIHOOD,
        )
    ]

    mock_llm.unambiguous_sic_code = AsyncMock(
        return_value=(mock_unambiguous_response, None)
    )

    # Test request without options
    request_data_without_options = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems",
        "org_description": "Electrical contracting company",
        "prompt_version": "v3",
    }

    response = client.post(
        "/v1/survey-assist/classify", json=request_data_without_options
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Verify that meta field is not present in the response
    assert "meta" not in data

    # Test request with options to verify meta field is included
    request_data_with_options = {
        "llm": "chat-gpt",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing and maintaining electrical systems",
        "org_description": "Electrical contracting company",
        "options": {"sic": {"rephrased": True}},
        "prompt_version": "v3",
    }

    response = client.post("/v1/survey-assist/classify", json=request_data_with_options)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Verify that meta field is present in the response when options are provided
    assert "meta" in data
    assert data["meta"] is not None
