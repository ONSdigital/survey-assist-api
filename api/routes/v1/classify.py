"""Module that provides the classification endpoint for the Survey Assist API.

This module contains the classification endpoint for the Survey Assist API.
It defines the classification endpoint and returns classification results using
vector store and LLM.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from industrial_classification_utils.llm.llm import ClassificationLLM

# from occupational_classification_utils.llm.llm import ClassificationLLM as SOCClassificationLLM
from survey_assist_utils.logging import get_logger

from api.models.classify import (
    ClassificationRequest,
    GenericCandidate,
    GenericClassificationResponse,
    GenericClassificationResult,
)
from api.services.sic_rephrase_client import SICRephraseClient
from api.services.sic_vector_store_client import SICVectorStoreClient
from api.services.soc_vector_store_client import SOCVectorStoreClient

router: APIRouter = APIRouter(tags=["Classification"])
logger = get_logger(__name__)


def get_sic_vector_store_client() -> SICVectorStoreClient:
    """Get a SIC vector store client instance.

    Returns:
        SICVectorStoreClient: A SIC vector store client instance.
    """
    return SICVectorStoreClient()


def get_soc_vector_store_client() -> SOCVectorStoreClient:
    """Get a SOC vector store client instance.

    Returns:
        SOCVectorStoreClient: A SOC vector store client instance.
    """
    return SOCVectorStoreClient()


def get_rephrase_client() -> SICRephraseClient:
    """Get a SIC rephrase client instance.

    Returns:
        SICRephraseClient: A SIC rephrase client instance.
    """
    return SICRephraseClient()


def get_sic_llm_client(model_name: Optional[str] = None) -> Any:  # type: ignore
    """Get a SIC ClassificationLLM instance."""
    if ClassificationLLM is None:
        raise ImportError("ClassificationLLM could not be imported.")
    if model_name:
        return ClassificationLLM(model_name=model_name)
    return ClassificationLLM()


def get_soc_llm_client(model_name: Optional[str] = None) -> Any:  # type: ignore
    """Get a SOC ClassificationLLM instance."""
    # TODO: Implement proper SOC LLM client when dependencies are available  # pylint: disable=fixme
    raise NotImplementedError("SOC LLM client not yet implemented")


# Define dependencies at module level
sic_vector_store_dependency = Depends(get_sic_vector_store_client)
soc_vector_store_dependency = Depends(get_soc_vector_store_client)
rephrase_dependency = Depends(get_rephrase_client)
sic_llm_dependency = Depends(get_sic_llm_client)
soc_llm_dependency = Depends(get_soc_llm_client)


@router.post("/classify", response_model=GenericClassificationResponse)
async def classify_text(
    request: Request,
    classification_request: ClassificationRequest,
    sic_vector_store: SICVectorStoreClient = sic_vector_store_dependency,
    soc_vector_store: SOCVectorStoreClient = soc_vector_store_dependency,
    rephrase_client: SICRephraseClient = rephrase_dependency,
) -> GenericClassificationResponse:
    """Classify the provided text using the generic response format.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The request containing the text to classify.
        sic_vector_store (SICVectorStoreClient): SIC vector store client instance.
        soc_vector_store (SOCVectorStoreClient): SOC vector store client instance.
        rephrase_client (SICRephraseClient): SIC rephrase client instance.

    Returns:
        GenericClassificationResponse: A response containing the classification results in
        generic format.

    Raises:
        HTTPException: If the input is invalid or classification fails.
    """
    # Validate input
    if (
        not classification_request.job_title.strip()
        or not classification_request.job_description.strip()
    ):
        logger.error(
            "Empty job title or description provided in classification request"
        )
        raise HTTPException(
            status_code=400, detail="Job title and description cannot be empty"
        )

    results = []

    try:
        # Handle SIC classification
        if classification_request.type in ["sic", "sic_soc"]:
            sic_result = await _classify_sic(
                request, classification_request, sic_vector_store, rephrase_client
            )
            results.append(sic_result)

        # Handle SOC classification
        if classification_request.type in ["soc", "sic_soc"]:
            soc_result = await _classify_soc(
                request, classification_request, soc_vector_store
            )
            results.append(soc_result)

        return GenericClassificationResponse(
            requested_type=classification_request.type,
            results=results,
        )

    except Exception as e:
        logger.error("Error in classify endpoint", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error during classification: {e!s}",
        ) from e


async def _classify_sic(  # pylint: disable=unused-argument
    request: Request,
    classification_request: ClassificationRequest,
    vector_store: SICVectorStoreClient,
    rephrase_client: SICRephraseClient,
) -> GenericClassificationResult:
    """Classify using SIC classification.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The classification request.
        vector_store (SICVectorStoreClient): SIC vector store client.
        rephrase_client (SICRephraseClient): SIC rephrase client.

    Returns:
        GenericClassificationResult: SIC classification result.
    """
    # Get vector store search results
    search_results = await vector_store.search(
        industry_descr=classification_request.org_description,
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
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

    # Get LLM instance and call sa_rag_sic_code
    llm = request.app.state.gemini_llm
    llm_response, _, actual_prompt = (  # pylint: disable=unused-variable
        llm.sa_rag_sic_code(
            industry_descr=classification_request.org_description or "",
            job_title=classification_request.job_title,
            job_description=classification_request.job_description,
            short_list=short_list,
        )
    )

    # Map LLM response to generic format
    candidates = [
        GenericCandidate(
            code=c.sic_code,
            descriptive=c.sic_descriptive,
            likelihood=c.likelihood,
        )
        for c in getattr(llm_response, "sic_candidates", [])
    ]

    result = GenericClassificationResult(
        type="sic",
        classified=getattr(llm_response, "codable", False),
        followup=getattr(llm_response, "followup", None),
        code=getattr(llm_response, "sic_code", None),
        description=getattr(llm_response, "sic_descriptive", None),
        candidates=candidates,
        reasoning=getattr(llm_response, "reasoning", ""),
    )

    # Rephrase SIC candidates using the rephrase client
    if rephrase_client and candidates:
        try:
            rephrased_candidates = []
            for candidate in candidates:
                rephrased_text = rephrase_client.get_rephrased_description(
                    candidate.code
                )
                if rephrased_text:
                    rephrased_candidates.append(
                        GenericCandidate(
                            code=candidate.code,
                            descriptive=rephrased_text,
                            likelihood=candidate.likelihood,
                        )
                    )
                else:
                    # Keep original description if no rephrased version available
                    rephrased_candidates.append(candidate)
            result.candidates = rephrased_candidates
        except Exception as e:  # pylint: disable=broad-except
            logger.warning(f"Failed to rephrase SIC candidates: {e}")

    return result


async def _classify_soc(  # pylint: disable=unused-argument
    request: Request,  # pylint: disable=unused-argument
    classification_request: ClassificationRequest,
    vector_store: SOCVectorStoreClient,
) -> GenericClassificationResult:
    """Classify using SOC classification.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The classification request.
        vector_store (SOCVectorStoreClient): SOC vector store client.

    Returns:
        GenericClassificationResult: SOC classification result.
    """
    # Get vector store search results (currently unused but kept for future use)
    await vector_store.search(
        industry_descr=classification_request.org_description,
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
    )

    # For SOC, we'll use a simple approach for now
    # In a full implementation, you would use the SOC LLM client
    # This is a placeholder implementation

    # Create a mock SOC result for now
    # TODO: Implement proper SOC classification using SOC LLM client  # pylint: disable=fixme
    result = GenericClassificationResult(
        type="soc",
        classified=True,
        followup=None,
        code="9111",  # Placeholder SOC code
        description="Farm workers",  # Placeholder description
        candidates=[
            GenericCandidate(
                code="9111",
                descriptive="Farm workers",
                likelihood=1.0,
            )
        ],
        reasoning="Placeholder SOC classification reasoning",
    )

    return result
