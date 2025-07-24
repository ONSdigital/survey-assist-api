"""Module that provides the classification endpoint for the Survey Assist API.

This module contains the classification endpoint for the Survey Assist API.
It defines the classification endpoint and returns classification results using
vector store and LLM.
"""

# mypy: disable-error-code="import-not-found,assignment,misc"

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from industrial_classification_utils.llm.llm import (
    ClassificationLLM as SICClassificationLLM,
)
from survey_assist_utils.logging import get_logger

from api.models.classify import (
    Candidate,
    ClassificationRequest,
    ClassificationResponse,
    ClassificationResult,
    ClassificationType,
)
from api.models.soc_classify import SocCandidate, SocClassificationResponse
from api.services.sic_rephrase_client import SICRephraseClient
from api.services.sic_vector_store_client import SICVectorStoreClient
from api.services.soc_llm_service import SOCLLMService
from api.services.soc_vector_store_client import SOCVectorStoreClient

# Import SOC classification LLM with fallback
try:
    from occupational_classification_utils.llm.llm import (
        ClassificationLLM as SOCClassificationLLM,
    )
except ImportError:
    SOCClassificationLLM = None

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
    if SICClassificationLLM is None:
        raise ImportError("SICClassificationLLM could not be imported.")
    if model_name:
        return SICClassificationLLM(model_name=model_name)
    return SICClassificationLLM()


# Define dependencies at module level
sic_vector_store_dependency = Depends(get_sic_vector_store_client)
soc_vector_store_dependency = Depends(get_soc_vector_store_client)
rephrase_dependency = Depends(get_rephrase_client)
llm_dependency = Depends(get_llm_client)


@router.post("/classify", response_model=ClassificationResponse)
async def classify_text(
    request: Request,
    classification_request: ClassificationRequest,
    sic_vector_store: SICVectorStoreClient = sic_vector_store_dependency,
    soc_vector_store: SOCVectorStoreClient = soc_vector_store_dependency,
    rephrase_client: SICRephraseClient = rephrase_dependency,
) -> ClassificationResponse:
    """Classify the provided text.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The request containing the text to classify.
        sic_vector_store (SICVectorStoreClient): SIC vector store client instance.
        soc_vector_store (SOCVectorStoreClient): SOC vector store client instance.
        rephrase_client (SICRephraseClient): SIC rephrase client instance.

    Returns:
        ClassificationResponse: A response containing the classification results.

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
        results = []

        # Handle different classification types
        if classification_request.type == ClassificationType.SIC:
            sic_result = await _classify_sic(
                request, classification_request, sic_vector_store
            )

            # Apply rephrased descriptions to the SIC response
            sic_result_dict = sic_result.model_dump()
            rephrased_result_dict = rephrase_client.process_classification_response(
                sic_result_dict
            )

            # Convert rephrased result back to new format
            # The rephrase client doesn't add a 'classified' field, so we need to determine it
            # from the sic_code
            is_classified = bool(
                rephrased_result_dict.get("sic_code")
                and rephrased_result_dict.get("sic_code") != "N/A"
            )
            sic_result = ClassificationResult(
                type="sic",
                classified=is_classified,
                followup=rephrased_result_dict["followup"],
                code=rephrased_result_dict.get("sic_code"),
                description=rephrased_result_dict.get("sic_description"),
                # Use candidates from original LLM response, not rephrase client
                candidates=sic_result.candidates,
                reasoning=rephrased_result_dict["reasoning"],
            )
            results.append(sic_result)

            logger.info(
                f"Applied rephrased descriptions to classification response. "
                f"Available rephrased descriptions: {rephrase_client.get_rephrased_count()}"
            )

        elif classification_request.type == ClassificationType.SOC:
            soc_result = await _classify_soc(
                request, classification_request, soc_vector_store
            )

            # Convert to generic format
            generic_result = ClassificationResult(
                type="soc",
                classified=soc_result.classified,
                followup=soc_result.followup,
                code=soc_result.soc_code,
                description=soc_result.soc_description,
                candidates=[
                    Candidate(
                        code=c.soc_code,
                        descriptive=c.soc_descriptive,
                        likelihood=c.likelihood,
                    )
                    for c in soc_result.soc_candidates
                ],
                reasoning=soc_result.reasoning,
            )
            results.append(generic_result)

        elif classification_request.type == ClassificationType.SIC_SOC:
            # Perform both SIC and SOC classifications
            sic_result = await _classify_sic(
                request, classification_request, sic_vector_store
            )

            # Apply rephrased descriptions to the SIC response
            sic_result_dict = sic_result.model_dump()
            rephrased_result_dict = rephrase_client.process_classification_response(
                sic_result_dict
            )

            # Convert rephrased result back to new format
            # The rephrase client doesn't add a 'classified' field, so we need to determine it
            # from the sic_code
            is_classified = bool(
                rephrased_result_dict.get("sic_code")
                and rephrased_result_dict.get("sic_code") != "N/A"
            )
            sic_result = ClassificationResult(
                type="sic",
                classified=is_classified,
                followup=rephrased_result_dict["followup"],
                code=rephrased_result_dict.get("sic_code"),
                description=rephrased_result_dict.get("sic_description"),
                # Use candidates from original LLM response, not rephrase client
                candidates=sic_result.candidates,
                reasoning=rephrased_result_dict["reasoning"],
            )
            results.append(sic_result)

            # Perform SOC classification
            soc_result = await _classify_soc(
                request, classification_request, soc_vector_store
            )

            # Convert SOC to generic format
            soc_generic_result = ClassificationResult(
                type="soc",
                classified=soc_result.classified,
                followup=soc_result.followup,
                code=soc_result.soc_code,
                description=soc_result.soc_description,
                candidates=[
                    Candidate(
                        code=c.soc_code,
                        descriptive=c.soc_descriptive,
                        likelihood=c.likelihood,
                    )
                    for c in soc_result.soc_candidates
                ],
                reasoning=soc_result.reasoning,
            )
            results.append(soc_generic_result)

        else:
            logger.error(
                "Unsupported classification type", type=classification_request.type
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported classification type: {classification_request.type}"
                ),
            )

        return ClassificationResponse(
            requested_type=classification_request.type.value,
            results=results,
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
) -> ClassificationResult:
    """Classify using SIC classification.

    Args:
        request: The FastAPI request object.
        classification_request: The classification request.
        vector_store: The SIC vector store client.

    Returns:
        ClassificationResult: The SIC classification result.
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
    llm_response, _, _ = llm.sa_rag_sic_code(
        industry_descr=classification_request.org_description or "",
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
        short_list=short_list,
    )

    # Map LLM response to generic format
    # SurveyAssistSicResponse has sic_candidates, not alt_candidates
    candidates = [
        Candidate(
            code=c.sic_code,
            descriptive=c.sic_descriptive,
            likelihood=c.likelihood,
        )
        for c in getattr(llm_response, "sic_candidates", [])
    ]

    return ClassificationResult(
        type="sic",
        classified=bool(
            getattr(llm_response, "sic_code", None)
            and getattr(llm_response, "sic_code", "") != "N/A"
        ),
        followup=getattr(llm_response, "followup", None),
        code=getattr(llm_response, "sic_code", None),
        description=getattr(llm_response, "sic_descriptive", None),
        candidates=candidates,
        reasoning=getattr(llm_response, "reasoning", ""),
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
    if SOCClassificationLLM is None:
        raise ImportError("SOCClassificationLLM could not be imported.")

    # Get vector store search results
    search_results = await vector_store.search(
        industry_descr=classification_request.org_description,
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
    )

    # Prepare shortlist for LLM (list of dicts with code/title/distance)
    short_list = [
        {
            "code": result["code"],
            "title": result["title"],
            "distance": result["distance"],
        }
        for result in search_results
    ]

    # Get SOC LLM instance from app state (pre-instantiated at startup)
    soc_llm = request.app.state.soc_llm
    soc_service = SOCLLMService(soc_llm)

    # Call the SOC LLM service using RAG approach with vector store results
    llm_response, _, _ = soc_service.sa_rag_soc_code(
        industry_descr=classification_request.org_description or "",
        job_title=classification_request.job_title,
        job_description=classification_request.job_description,
        short_list=short_list,
    )

    # Map LLM response to API response
    soc_candidates = getattr(llm_response, "soc_candidates", [])
    if not isinstance(soc_candidates, list):
        soc_candidates = []

    candidates = [
        SocCandidate(
            soc_code=c.soc_code,
            soc_descriptive=c.soc_descriptive,
            likelihood=c.likelihood,
        )
        for c in soc_candidates
    ]

    return SocClassificationResponse(
        classified=bool(getattr(llm_response, "classified", False)),
        followup=getattr(llm_response, "followup", None),
        soc_code=getattr(llm_response, "soc_code", None),
        soc_description=getattr(llm_response, "soc_description", None),
        soc_candidates=candidates,
        reasoning=getattr(llm_response, "reasoning", ""),
        prompt_used=getattr(llm_response, "prompt_used", None),
    )
