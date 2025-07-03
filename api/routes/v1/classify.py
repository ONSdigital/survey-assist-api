"""Module that provides the classification endpoint for the Survey Assist API.

This module contains the classification endpoint for the Survey Assist API.
It defines the classification endpoint and returns classification results using
vector store and LLM.
"""

from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request
from industrial_classification_utils.llm.llm import ClassificationLLM
from survey_assist_utils.logging import get_logger

from api.models.classify import (
    ClassificationRequest,
    ClassificationResponse,
    ClassificationType,
    SicCandidate,
)
from api.models.soc_classify import SocClassificationResponse
from api.services.sic_rephrase_client import SICRephraseClient
from api.services.sic_vector_store_client import SICVectorStoreClient
from api.services.soc_llm_service import SOCLLMService
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


def get_llm_client(model_name: Optional[str] = None) -> Any:  # type: ignore
    """Get a ClassificationLLM instance."""
    if ClassificationLLM is None:
        raise ImportError("ClassificationLLM could not be imported.")
    if model_name:
        return ClassificationLLM(model_name=model_name)
    return ClassificationLLM()


# Define dependencies at module level
sic_vector_store_dependency = Depends(get_sic_vector_store_client)
soc_vector_store_dependency = Depends(get_soc_vector_store_client)
rephrase_dependency = Depends(get_rephrase_client)
llm_dependency = Depends(get_llm_client)


@router.post(
    "/classify", response_model=Union[ClassificationResponse, SocClassificationResponse]
)
async def classify_text(
    request: Request,
    classification_request: ClassificationRequest,
    sic_vector_store: SICVectorStoreClient = sic_vector_store_dependency,
    soc_vector_store: SOCVectorStoreClient = soc_vector_store_dependency,
    rephrase_client: SICRephraseClient = rephrase_dependency,
) -> Union[ClassificationResponse, SocClassificationResponse]:
    """Classify the provided text.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The request containing the text to classify.
        sic_vector_store (SICVectorStoreClient): SIC vector store client instance.
        soc_vector_store (SOCVectorStoreClient): SOC vector store client instance.
        rephrase_client (SICRephraseClient): SIC rephrase client instance.

    Returns:
        Union[ClassificationResponse, SocClassificationResponse]: A response containing
        the classification results.

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
            status_code=400,
            detail="Job title and description cannot be empty",
        )

    try:
        # Handle different classification types
        if classification_request.type == ClassificationType.SIC:
            response = await _classify_sic(
                request, classification_request, sic_vector_store
            )
            
            # Apply rephrased descriptions to the SIC response
            response_dict = response.model_dump()
            rephrased_response_dict = rephrase_client.process_classification_response(
                response_dict
            )

            # Convert back to ClassificationResponse model
            rephrased_response = ClassificationResponse(**rephrased_response_dict)

            logger.info(
                f"Applied rephrased descriptions to classification response. "
                f"Available rephrased descriptions: {rephrase_client.get_rephrased_count()}"
            )

            return rephrased_response
            
        if classification_request.type == ClassificationType.SOC:
            return await _classify_soc(
                request, classification_request, soc_vector_store
            )
        logger.error(
            "Unsupported classification type", type=classification_request.type
        )
        raise HTTPException(
            status_code=400,
            detail=(f"Unsupported classification type: {classification_request.type}"),
        )

    except Exception as e:
        logger.error("Error in classify endpoint", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error during classification: {e!s}",
        ) from e


async def _classify_sic(
    request: Request,
    classification_request: ClassificationRequest,
    vector_store: SICVectorStoreClient,
) -> ClassificationResponse:
    """Classify using SIC classification.

    Args:
        request: The FastAPI request object.
        classification_request: The classification request.
        vector_store: The SIC vector store client.

    Returns:
        ClassificationResponse: The SIC classification response.
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
    llm_response, _, actual_prompt = llm.sa_rag_sic_code(
        industry_descr=classification_request.org_description or "",
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
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
        prompt_used=str(actual_prompt) if actual_prompt else None,
    )


async def _classify_soc(
    request: Request,
    classification_request: ClassificationRequest,
    vector_store: SOCVectorStoreClient,
) -> SocClassificationResponse:
    """Classify using SOC classification.

    Args:
        request: The FastAPI request object.
        classification_request: The classification request.
        vector_store: The SOC vector store client.

    Returns:
        SocClassificationResponse: The SOC classification response.
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

    # Get LLM instance and create SOC service
    llm = request.app.state.gemini_llm
    soc_service = SOCLLMService(llm)

    # Call SOC classification
    llm_response, _, _ = soc_service.sa_rag_soc_code(
        industry_descr=classification_request.org_description or "",
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
        short_list=short_list,
    )

    return llm_response
