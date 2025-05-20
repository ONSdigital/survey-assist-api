"""Module that provides the classification endpoint for the Survey Assist API.

This module contains the classification endpoint for the Survey Assist API.
It defines the classification endpoint and returns mocked classification results.
"""

from fastapi import APIRouter, HTTPException

from api.models.classify import (
    ClassificationRequest,
    ClassificationResponse,
    SicCandidate,
)

router: APIRouter = APIRouter(tags=["Classification"])


@router.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest) -> ClassificationResponse:
    """Classify the provided text.

    Args:
        request (ClassificationRequest): The request containing the text to classify.

    Returns:
        ClassificationResponse: A response containing the classification results.

    Raises:
        HTTPException: If the input is invalid.
    """
    # Validate input
    if not request.job_title.strip() or not request.job_description.strip():
        raise HTTPException(
            status_code=400, detail="Job title and description cannot be empty"
        )

    # Mock classification result
    mock_candidates = [
        SicCandidate(
            sic_code="43210", sic_descriptive="Electrical installation", likelihood=0.95
        ),
        SicCandidate(
            sic_code="43220",
            sic_descriptive=("Plumbing, heat and air-conditioning installation"),
            likelihood=0.03,
        ),
        SicCandidate(
            sic_code="43290",
            sic_descriptive=("Other construction installation"),
            likelihood=0.02,
        ),
    ]

    return ClassificationResponse(
        classified=True,
        followup=None,
        sic_code="43210",
        sic_description="Electrical installation",
        sic_candidates=mock_candidates,
        reasoning=(
            "Based on the job title and description, this is clearly an electrical "
            "installation role. The primary activities involve installing and "
            "maintaining electrical systems in buildings, which aligns with SIC code 43210."
        ),
    )
