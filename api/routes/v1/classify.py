"""Module that provides the classification endpoint for the Survey Assist API.

This module contains the classification endpoint for the Survey Assist API.
It defines the classification endpoint and returns classification results using
vector store and LLM.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from industrial_classification_utils.llm.llm import ClassificationLLM
from survey_assist_utils.logging import get_logger

from api.models.classify import (
    ClassificationRequest,
    ClassificationResponse,
    LLMModel,
    SicCandidate,
)
from api.services.sic_vector_store_client import SICVectorStoreClient

router: APIRouter = APIRouter(tags=["Classification"])
logger = get_logger(__name__)
std_logger = logging.getLogger(__name__)


def get_vector_store_client() -> SICVectorStoreClient:
    """Get a vector store client instance.

    Returns:
        SICVectorStoreClient: A vector store client instance.
    """
    return SICVectorStoreClient()


def get_llm_client(model_name: Optional[str] = None) -> Any:  # type: ignore
    """Get a ClassificationLLM instance."""
    if ClassificationLLM is None:
        raise ImportError("ClassificationLLM could not be imported.")
    if model_name:
        return ClassificationLLM(model_name=model_name)
    return ClassificationLLM()


# Define dependencies at module level
vector_store_dependency = Depends(get_vector_store_client)
llm_dependency = Depends(get_llm_client)


@router.post("/classify", response_model=ClassificationResponse)
async def classify_text(
    request: ClassificationRequest,
    vector_store: SICVectorStoreClient = vector_store_dependency,
) -> ClassificationResponse:
    """Classify the provided text.

    Args:
        request (ClassificationRequest): The request containing the text to classify.
        vector_store (SICVectorStoreClient): Vector store client instance.

    Returns:
        ClassificationResponse: A response containing the classification results.

    Raises:
        HTTPException: If the input is invalid or classification fails.
    """
    # Validate input
    if not request.job_title.strip() or not request.job_description.strip():
        logger.error(
            "Empty job title or description provided in classification request"
        )
        raise HTTPException(
            status_code=400, detail="Job title and description cannot be empty"
        )

    try:
        # Get vector store search results
        search_results = await vector_store.search(
            industry_descr=request.org_description,
            job_title=request.job_title,
            job_description=request.job_description,
        )

        # Prepare shortlist for LLM (list of dicts with code/title/likelihood)
        short_list = [
            {
                "code": result["code"],
                "title": result["title"],
                "distance": result["distance"],
            }
            for result in search_results
        ]

        # Determine model name
        model_name = "gemini-1.5-flash" if request.llm == LLMModel.GEMINI else "gpt-4"

        # Instantiate LLM with the correct model_name
        llm = get_llm_client(model_name=model_name)

        # Call LLM using sa_rag_sic_code (no model_name argument)
        llm_response, _, _ = llm.sa_rag_sic_code(
            industry_descr=request.org_description or "",
            job_title=request.job_title,
            job_description=request.job_description,
            short_list=short_list,
        )

        # Map LLM response to API response
        candidates = [
            SicCandidate(
                sic_code=c.class_code,
                sic_descriptive=c.class_descriptive,
                likelihood=c.likelihood,
            )
            for c in getattr(llm_response, "alt_candidates", [])
        ]

        return ClassificationResponse(
            classified=bool(getattr(llm_response, "classified", False)),
            followup=getattr(llm_response, "followup", None),
            sic_code=getattr(llm_response, "class_code", None),
            sic_description=getattr(llm_response, "class_descriptive", None),
            sic_candidates=candidates,
            reasoning=getattr(llm_response, "reasoning", ""),
        )

    except Exception as e:
        std_logger.error("Error during classification: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Error during classification: {e!s}",
        ) from e
