"""Tests for the classification endpoint.

This module contains tests for the classification endpoint of the Survey Assist API.
"""

from fastapi import status
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_classify_endpoint_success():
    """Test successful classification request."""
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


def test_classify_endpoint_empty_input():
    """Test classification request with empty input."""
    response = client.post(
        "/v1/survey-assist/classify",
        json={
            "llm": "chat-gpt",
            "type": "sic",
            "job_title": "",
            "job_description": "",
            "org_description": "Electrical contracting company",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Job title and description cannot be empty"


def test_classify_endpoint_invalid_json():
    """Test classification request with invalid JSON."""
    response = client.post(
        "/v1/survey-assist/classify",
        json={"invalid": "data"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_classify_endpoint_invalid_llm():
    """Test classification request with invalid LLM model."""
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
    """Test classification request with invalid classification type."""
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
