"""Tests for generic classification format and combined SIC-SOC classification.

This module tests the unified classification response format and the combined
SIC-SOC classification functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Constants for testing
EXPECTED_RESULTS_COUNT = 1  # SIC only should return 1 result


@pytest.mark.api
@patch("api.routes.v1.classify.SICRephraseClient")
@patch("api.routes.v1.classify.SICVectorStoreClient")
@patch("api.main.app.state.gemini_llm")
@patch("google.auth.default")
def test_generic_classification_format(
    mock_auth, mock_llm, mock_vector_store, mock_rephrase_client
):
    """Test the generic ClassificationResponse format structure.

    This test verifies that:
    1. The response follows the ClassificationResponse model structure
    2. Candidate objects have the correct field names (descriptive, not description)
    3. All required fields are present in the response
    """
    # Mock authentication
    mock_auth.return_value = (MagicMock(), "test-project")

    # Mock vector store search results
    mock_vector_store.return_value.search = AsyncMock(
        return_value=[
            {
                "code": "43210",
                "title": "Electrical installation",
                "distance": 0.05,
            }
        ]
    )

    # Mock LLM responses
    mock_llm.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=True,
            class_code="43210",
            class_descriptive="Electrical installation",
            reasoning="Based on job title",
            followup=None,
            alt_candidates=[
                MagicMock(
                    class_code="43210",
                    class_descriptive="Electrical installation",
                    likelihood=0.95,
                )
            ],
        ),
        None,
        None,
    )

    # Mock rephrase client
    mock_rephrase_instance = MagicMock()
    mock_rephrase_instance.process_classification_response.return_value = {
        "classified": True,
        "followup": None,
        "sic_code": "43210",
        "sic_description": "Electrical installation",
        "sic_candidates": [
            {
                "sic_code": "43210",
                "sic_descriptive": "Electrical installation",
                "likelihood": 0.95,
            }
        ],
        "reasoning": "Mocked reasoning",
    }
    mock_rephrase_instance.get_rephrased_count.return_value = 0
    mock_rephrase_client.return_value = mock_rephrase_instance

    # Test request
    request_data = {
        "llm": "gemini",
        "type": "sic",
        "job_title": "Electrician",
        "job_description": "Installing electrical systems",
        "org_description": "Construction company",
    }

    response = client.post("/v1/survey-assist/classify", json=request_data)

    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check generic response structure
    assert data["requested_type"] == "sic"
    assert "results" in data
    assert len(data["results"]) == EXPECTED_RESULTS_COUNT

    # Check result structure
    result = data["results"][0]
    assert result["type"] == "sic"
    assert "classified" in result
    assert "code" in result
    assert "description" in result
    assert "candidates" in result
    assert "reasoning" in result

    # Check candidate structure (should use 'descriptive' field)
    if result["candidates"]:
        candidate = result["candidates"][0]
        assert "code" in candidate
        assert "descriptive" in candidate  # Not 'description'
        assert "likelihood" in candidate
