"""Tests for SOC classification functionality.

This module contains tests for the SOC classification endpoint and related services.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models.classify import ClassificationRequest, ClassificationType, LLMModel
from api.models.soc_classify import SocCandidate, SocClassificationResponse
from api.services.soc_vector_store_client import SOCVectorStoreClient

# Constants for testing
EXPECTED_LIKELIHOOD = 0.85
EXPECTED_RESULTS_COUNT = 2
EXPECTED_DISTANCE_1 = 0.123
EXPECTED_DISTANCE_2 = 0.456


class TestSOCClassification:
    """Test cases for SOC classification functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_soc_vector_store(self):
        """Mock SOC vector store responses."""
        with patch(
            "api.services.soc_vector_store_client.SOCVectorStoreClient.search"
        ) as mock_search:
            mock_search.return_value = [
                {
                    "code": "5241",
                    "title": "Electricians and Electrical Fitters",
                    "distance": EXPECTED_DISTANCE_1,
                },
                {
                    "code": "5242",
                    "title": "Telecommunications Engineers",
                    "distance": EXPECTED_DISTANCE_2,
                },
            ]
            yield mock_search

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for SOC classification."""
        mock_response = MagicMock()
        mock_response.followup = "What specific electrical work do you do?"
        mock_response.soc_code = "5241"
        mock_response.soc_descriptive = "Electricians and Electrical Fitters"
        mock_response.reasoning = "Based on job title and description"
        mock_response.soc_candidates = [
            MagicMock(
                soc_code="5241",
                likelihood=EXPECTED_LIKELIHOOD,
                soc_descriptive="Electricians and Electrical Fitters",
            )
        ]
        return mock_response

    def test_soc_classification_request_model(self):
        """Test SOC classification request model."""
        request = ClassificationRequest(
            llm=LLMModel.GEMINI,
            type=ClassificationType.SOC,
            job_title="Electrician",
            job_description="Install and maintain electrical systems",
            org_description="Construction company",
        )
        assert request.type == ClassificationType.SOC
        assert request.job_title == "Electrician"
        assert request.job_description == "Install and maintain electrical systems"
        assert request.org_description == "Construction company"

    def test_soc_classification_response_model(self):
        """Test SOC classification response model."""
        response = SocClassificationResponse(
            classified=True,
            followup=None,
            soc_code="5241",
            soc_description="Electricians and Electrical Fitters",
            soc_candidates=[
                SocCandidate(
                    soc_code="5241",
                    soc_descriptive="Electricians and Electrical Fitters",
                    likelihood=EXPECTED_LIKELIHOOD,
                ),
            ],
            reasoning="Test reasoning",
            prompt_used="Test prompt",
        )
        assert response.classified is True
        assert response.soc_code == "5241"
        assert response.soc_description == "Electricians and Electrical Fitters"
        assert len(response.soc_candidates) == 1
        assert response.soc_candidates[0].soc_code == "5241"
        assert response.soc_candidates[0].likelihood == EXPECTED_LIKELIHOOD


class TestSOCVectorStoreClient:
    """Test cases for SOC vector store client."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for testing."""
        with patch(
            "api.services.soc_vector_store_client.httpx.AsyncClient"
        ) as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "code": "5241",
                        "title": "Electricians and Electrical Fitters",
                        "distance": EXPECTED_DISTANCE_1,
                    },
                    {
                        "code": "5242",
                        "title": "Telecommunications Engineers",
                        "distance": EXPECTED_DISTANCE_2,
                    },
                ]
            }
            mock_response.raise_for_status.return_value = None

            # Create async mock methods
            async def async_post(*args, **kwargs):  # pylint: disable=unused-argument
                return mock_response

            async def async_get(*args, **kwargs):  # pylint: disable=unused-argument
                return mock_response

            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post = async_post
            mock_client_instance.get = async_get
            mock_client.return_value = mock_client_instance
            yield mock_client

    @pytest.mark.asyncio
    async def test_soc_vector_store_search_success(
        self, mock_httpx_client
    ):  # pylint: disable=unused-argument
        """Test successful SOC vector store search."""
        client = SOCVectorStoreClient()
        results = await client.search(
            industry_descr="Construction company",
            job_title="Electrician",
            job_description="Install and maintain electrical systems",
        )
        assert len(results) == EXPECTED_RESULTS_COUNT
        assert results[0]["code"] == "5241"
        assert results[0]["title"] == "Electricians and Electrical Fitters"
        assert results[0]["distance"] == EXPECTED_DISTANCE_1
        assert results[1]["code"] == "5242"
        assert results[1]["title"] == "Telecommunications Engineers"
        assert results[1]["distance"] == EXPECTED_DISTANCE_2

    @pytest.mark.asyncio
    async def test_soc_vector_store_get_status_success(
        self, mock_httpx_client
    ):  # pylint: disable=unused-argument
        """Test successful SOC vector store status check."""
        client = SOCVectorStoreClient()
        status = await client.get_status()
        assert status == {
            "results": [
                {
                    "code": "5241",
                    "title": "Electricians and Electrical Fitters",
                    "distance": EXPECTED_DISTANCE_1,
                },
                {
                    "code": "5242",
                    "title": "Telecommunications Engineers",
                    "distance": EXPECTED_DISTANCE_2,
                },
            ]
        }
