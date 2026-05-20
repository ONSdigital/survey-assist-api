"""Module that provides the classification endpoint for the Survey Assist API.

This module contains the classification endpoint for the Survey Assist API.
It defines the classification endpoint and returns classification results using
vector store and LLM.
"""

import os
import time
from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request
from industrial_classification_utils.llm.llm import ClassificationLLM
from survey_assist_utils.logging import get_logger

from api.models.classify import (
    AppliedOptions,
    ClassificationRequest,
    GenericCandidate,
    GenericClassificationResponse,
    GenericClassificationResponseWithoutMeta,
    GenericClassificationResult,
    ResponseMeta,
)
from api.services.sic_rephrase_client import SICRephraseClient
from api.services.sic_vector_store_client import SICVectorStoreClient
from api.services.soc_rephrase_client import SOCRephraseClient
from api.services.soc_vector_store_client import SOCVectorStoreClient
from utils.survey import truncate_identifier

router: APIRouter = APIRouter(tags=["Classification"])
logger = get_logger(__name__)

MAX_LEN = 12


def get_sic_vector_store_client() -> SICVectorStoreClient:
    """Get a SIC vector store client instance.

    Returns:
        SICVectorStoreClient: A SIC vector store client instance.
    """
    env_url = os.getenv("SIC_VECTOR_STORE")
    if env_url and env_url.strip():
        logger.info(f"Using SIC vector store URL from environment: {env_url}")
        return SICVectorStoreClient(base_url=env_url.strip())

    logger.warning(
        "SIC_VECTOR_STORE environment variable not set, using default localhost URL"
    )
    return SICVectorStoreClient()


def get_soc_vector_store_client() -> SOCVectorStoreClient:
    """Get a SOC vector store client instance.

    Returns:
        SOCVectorStoreClient: A SOC vector store client instance.
    """
    env_url = os.getenv("SOC_VECTOR_STORE")
    if env_url and env_url.strip():
        logger.info(f"Using SOC vector store URL from environment: {env_url}")
        return SOCVectorStoreClient(base_url=env_url.strip())

    logger.warning(
        "SOC_VECTOR_STORE environment variable not set, using default localhost URL"
    )
    return SOCVectorStoreClient()


def get_rephrase_client(request: Request) -> SICRephraseClient:
    """Get a SIC rephrase client instance.

    Args:
        request: The FastAPI request object containing the app state.

    Returns:
        SICRephraseClient: A SIC rephrase client instance.
    """
    return request.app.state.sic_rephrase_client


def get_soc_rephrase_client(request: Request) -> SOCRephraseClient:
    """Get the SOC rephrase client instance.

    Args:
        request: The FastAPI request object containing the app state.

    Returns:
        SOCRephraseClient: The SOC rephrase client (index naming and mapping).
    """
    return request.app.state.soc_rephrase_client


def get_sic_llm_client(model_name: Optional[str] = None) -> Any:  # type: ignore
    """Get a SIC ClassificationLLM instance."""
    if ClassificationLLM is None:
        raise ImportError("ClassificationLLM could not be imported.")
    if model_name:
        return ClassificationLLM(model_name=model_name)
    return ClassificationLLM()


def get_soc_llm_client(request: Request) -> Any:  # type: ignore
    """Get the SOC ClassificationLLM from app state (mirrors SIC via gemini_llm)."""
    return request.app.state.soc_llm


# Define dependencies at module level
sic_vector_store_dependency = Depends(get_sic_vector_store_client)
soc_vector_store_dependency = Depends(get_soc_vector_store_client)
rephrase_dependency = Depends(get_rephrase_client)
soc_rephrase_dependency = Depends(get_soc_rephrase_client)
sic_llm_dependency = Depends(get_sic_llm_client)
soc_llm_dependency = Depends(get_soc_llm_client)


@router.post(
    "/classify",
    response_model=Union[
        GenericClassificationResponse, GenericClassificationResponseWithoutMeta
    ],
)
async def classify_text(
    request: Request,
    classification_request: ClassificationRequest,
    sic_vector_store: SICVectorStoreClient = sic_vector_store_dependency,
    soc_vector_store: SOCVectorStoreClient = soc_vector_store_dependency,
    rephrase_client: SICRephraseClient = rephrase_dependency,
    soc_rephrase_client: SOCRephraseClient = soc_rephrase_dependency,
) -> Union[GenericClassificationResponse, GenericClassificationResponseWithoutMeta]:
    """Classify the provided text using the generic response format.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The request containing the text to classify.
        sic_vector_store (SICVectorStoreClient): SIC vector store client instance.
        soc_vector_store (SOCVectorStoreClient): SOC vector store client instance.
        rephrase_client (SICRephraseClient): SIC rephrase client instance.
        soc_rephrase_client (SOCRephraseClient): SOC rephrase client instance.

    Returns:
        GenericClassificationResponse: A response containing the classification results in
        generic format.

    Raises:
        HTTPException: If the input is invalid or classification fails.
    """
    # Validate input
    start_time = time.perf_counter()
    body_id = (
        truncate_identifier(classification_request.job_title)
        + truncate_identifier(classification_request.job_description)
        + truncate_identifier(classification_request.org_description)
    )
    logger.info(
        "Request received for classify",
        type=classification_request.type,
        body_id=body_id,
        job_title=truncate_identifier(classification_request.job_title),
        job_description=truncate_identifier(classification_request.job_description),
        org_description=truncate_identifier(classification_request.org_description),
    )
    if (
        not classification_request.job_title.strip()
        or not classification_request.job_description.strip()
    ):
        logger.error(
            "Empty job title or description provided in classification request",
            body_id=body_id,
        )
        raise HTTPException(
            status_code=400, detail="Job title and description cannot be empty"
        )

    results = []

    try:
        # Handle SIC classification
        if classification_request.type in ["sic", "sic_soc"]:
            sic_result = await _classify_sic(
                request,
                classification_request,
                sic_vector_store,
                rephrase_client,
                body_id,
            )
            results.append(sic_result)

        # Handle SOC classification
        if classification_request.type in ["soc", "sic_soc"]:
            soc_result = await _classify_soc(
                request,
                classification_request,
                soc_vector_store,
                soc_rephrase_client,
                body_id,
            )
            results.append(soc_result)

        # Build meta response if options were provided
        meta = None
        if classification_request.options:
            applied_options = AppliedOptions()

            # Add SIC options if SIC classification was performed
            if (
                classification_request.type in ["sic", "sic_soc"]
                and classification_request.options.sic
            ):
                applied_options.sic = {
                    "rephrased": classification_request.options.sic.rephrased
                }

            # Add SOC options if SOC classification was performed
            if (
                classification_request.type in ["soc", "sic_soc"]
                and classification_request.options.soc
            ):
                applied_options.soc = {
                    "rephrased": classification_request.options.soc.rephrased
                }

            meta = ResponseMeta(
                llm=classification_request.llm, applied_options=applied_options
            )

        # Build response without meta field if it's None
        if meta is None:
            response_obj: Union[
                GenericClassificationResponse, GenericClassificationResponseWithoutMeta
            ] = GenericClassificationResponseWithoutMeta(
                requested_type=classification_request.type,
                results=results,
            )
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                "Response sent for classify",
                requested_type=classification_request.type,
                results_count=len(results),
                body_id=body_id,
                duration_ms=str(duration_ms),
            )
            return response_obj
        response_obj = GenericClassificationResponse(
            requested_type=classification_request.type,
            results=results,
            meta=meta,
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "Response sent for classify",
            requested_type=classification_request.type,
            results_count=len(results),
            has_meta=str(meta is not None),
            body_id=body_id,
            duration_ms=str(duration_ms),
        )
        return response_obj

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in classify endpoint", error=str(e), body_id=body_id)
        raise HTTPException(
            status_code=500,
            detail=f"Error during classification: {e!s}",
        ) from e


async def _classify_sic(  # pylint: disable=unused-argument,too-many-locals
    request: Request,
    classification_request: ClassificationRequest,
    vector_store: SICVectorStoreClient,
    rephrase_client: SICRephraseClient,
    body_id: str,
) -> GenericClassificationResult:
    """Classify using SIC classification with two-step process.

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The classification request.
        vector_store (SICVectorStoreClient): SIC vector store client.
        rephrase_client (SICRephraseClient): SIC rephrase client.
        body_id (str): Pseudo correlation ID built from truncated request fields.

    Returns:
        GenericClassificationResult: SIC classification result.

    Raises:
        HTTPException: If the two-step process fails with 422 status.
    """
    try:
        # Get vector store search results
        search_results = await vector_store.search(
            industry_descr=classification_request.org_description,
            job_title=classification_request.job_title,
            job_description=classification_request.job_description,
            correlation_id=body_id,
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

        # Get LLM instance
        llm = request.app.state.gemini_llm

        # Step 1: Call unambiguous SIC code classification
        logger.info(
            f"LLM request sent for unambiguous SIC classification - "
            f"job_title: '{truncate_identifier(classification_request.job_title)}', "
            f"job_description: '{truncate_identifier(classification_request.job_description)}', "
            f"org_description: '{truncate_identifier(classification_request.org_description)}'",
            body_id=body_id,
        )
        try:
            llm_start = time.perf_counter()
            unambiguous_response, _ = await llm.unambiguous_sic_code(
                industry_descr=classification_request.org_description or "",
                semantic_search_results=short_list,
                job_title=classification_request.job_title,
                job_description=classification_request.job_description,
            )
            llm_duration_ms = int((time.perf_counter() - llm_start) * 1000)
            logger.info(
                "LLM response received for unambiguous sic prompt",
                codable=str(bool(getattr(unambiguous_response, "codable", False))),
                selected_code=(
                    str(getattr(unambiguous_response, "class_code", ""))
                    if bool(getattr(unambiguous_response, "codable", False))
                    else ""
                ),
                alt_candidates_count=str(
                    len(getattr(unambiguous_response, "alt_candidates", []) or [])
                ),
                duration_ms=str(llm_duration_ms),
                body_id=body_id,
            )
        except Exception as e:
            logger.error(
                "Error in unambiguous SIC classification", error=str(e), body_id=body_id
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "type": "classification_error",
                        "message": "The LLM could not generate a valid classification",
                        "details": f"Unambiguous classification failed: {e!s}",
                    }
                },
            ) from e

        # Check if unambiguous classification found a match
        if unambiguous_response.codable and unambiguous_response.class_code:
            # SIC code found - return response with found code and candidates
            candidates = [
                GenericCandidate(
                    code=c.class_code,
                    descriptive=c.class_descriptive,
                    likelihood=c.likelihood,
                )
                for c in unambiguous_response.alt_candidates
            ]

            result = GenericClassificationResult(
                type="sic",
                classified=True,
                followup=None,  # No follow-up question needed
                code=unambiguous_response.class_code,
                description=unambiguous_response.class_descriptive,
                candidates=candidates,
                reasoning=unambiguous_response.reasoning,
            )
        else:
            # No unambiguous match found - call formulate open question
            job_title_trunc = truncate_identifier(classification_request.job_title)
            job_desc_trunc = truncate_identifier(classification_request.job_description)
            org_desc_trunc = truncate_identifier(classification_request.org_description)
            logger.info(
                f"LLM request sent to formulate open question - "
                f"job_title: '{job_title_trunc}', "
                f"job_description: '{job_desc_trunc}', "
                f"org_description: '{org_desc_trunc}'",
                body_id=body_id,
            )
            try:
                # Pass all alt_candidates for the open question
                llm_start2 = time.perf_counter()
                open_question_response, _ = await llm.formulate_open_question(
                    industry_descr=classification_request.org_description or "",
                    job_title=classification_request.job_title,
                    job_description=classification_request.job_description,
                    llm_output=unambiguous_response.alt_candidates,
                )
                llm_duration2_ms = int((time.perf_counter() - llm_start2) * 1000)
                logger.info(
                    "LLM response received for open question prompt",
                    has_followup=str(
                        bool(getattr(open_question_response, "followup", None))
                    ),
                    duration_ms=str(llm_duration2_ms),
                    body_id=body_id,
                )
            except Exception as e:
                logger.error(
                    "Error in formulate open question", error=str(e), body_id=body_id
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": {
                            "type": "classification_error",
                            "message": "The LLM could not generate a valid classification",
                            "details": f"Open question formulation failed: {e!s}",
                        }
                    },
                ) from e

            # Map candidates from unambiguous response
            candidates = [
                GenericCandidate(
                    code=c.class_code,
                    descriptive=c.class_descriptive,
                    likelihood=c.likelihood,
                )
                for c in unambiguous_response.alt_candidates
            ]

            result = GenericClassificationResult(
                type="sic",
                classified=False,  # No matching SIC code found
                followup=open_question_response.followup,
                code=None,  # No matching SIC code
                description=None,  # No matching SIC code
                candidates=candidates,
                reasoning=unambiguous_response.reasoning,
            )

        # Apply rephrasing if enabled
        if rephrase_client and candidates:
            result.candidates = _apply_rephrasing(
                candidates, rephrase_client, classification_request
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error("Unexpected error in SIC classification", error=str(e))
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "type": "classification_error",
                    "message": "The LLM could not generate a valid classification",
                    "details": f"Response was empty or invalid JSON: {e!s}",
                }
            },
        ) from e


def _apply_rephrasing(
    candidates: list[GenericCandidate],
    rephrase_client: SICRephraseClient,
    classification_request: ClassificationRequest,
) -> list[GenericCandidate]:
    """Apply rephrasing to SIC candidates if enabled.

    Args:
        candidates: List of SIC candidates to potentially rephrase.
        rephrase_client: The rephrase client instance.
        classification_request: The classification request containing options.

    Returns:
        List of candidates with rephrased descriptions if enabled.
    """
    # Check if SIC rephrasing is enabled (default to True for backward compatibility)
    rephrasing_enabled = (
        classification_request.options.sic.rephrased
        if classification_request.options and classification_request.options.sic
        else True
    )

    if not rephrasing_enabled:
        return candidates

    try:
        rephrased_candidates = []
        for candidate in candidates:
            rephrased_text = rephrase_client.get_rephrased_description(candidate.code)
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
                logger.debug(
                    f"No rephrased description found for SIC code {candidate.code}, "
                    "keeping original description"
                )
                rephrased_candidates.append(candidate)
        return rephrased_candidates
    except Exception as e:  # pylint: disable=broad-except
        logger.warning(f"Failed to rephrase SIC candidates: {e}")
        return candidates


def _apply_soc_rephrasing(
    candidates: list[GenericCandidate],
    soc_rephrase_client: SOCRephraseClient,
    classification_request: ClassificationRequest,
) -> list[GenericCandidate]:
    """Apply rephrasing to SOC candidates if enabled (mirrors ``_apply_rephrasing``)."""
    rephrasing_enabled = (
        classification_request.options.soc.rephrased
        if classification_request.options and classification_request.options.soc
        else True
    )

    if not rephrasing_enabled:
        return candidates

    try:
        rephrased_candidates = []
        for candidate in candidates:
            rephrased_text = soc_rephrase_client.get_rephrased_description(candidate.code)
            if rephrased_text:
                rephrased_candidates.append(
                    GenericCandidate(
                        code=candidate.code,
                        descriptive=rephrased_text,
                        likelihood=candidate.likelihood,
                    )
                )
            else:
                logger.debug(
                    f"No rephrased description found for SOC code {candidate.code}, "
                    "keeping original description"
                )
                rephrased_candidates.append(candidate)
        return rephrased_candidates
    except Exception as e:  # pylint: disable=broad-except
        logger.warning(f"Failed to rephrase SOC candidates: {e}")
        return candidates


async def _classify_soc(  # pylint: disable=unused-argument,too-many-locals
    request: Request,
    classification_request: ClassificationRequest,
    vector_store: SOCVectorStoreClient,
    soc_rephrase_client: SOCRephraseClient,
    body_id: str,
) -> GenericClassificationResult:
    """Classify using SOC classification with two-step process (mirrors ``_classify_sic``).

    Args:
        request (Request): The FastAPI request object.
        classification_request (ClassificationRequest): The classification request.
        vector_store (SOCVectorStoreClient): SOC vector store client.
        soc_rephrase_client (SOCRephraseClient): SOC rephrase client.
        body_id (str): Pseudo correlation ID built from truncated request fields.

    Returns:
        GenericClassificationResult: SOC classification result.

    Raises:
        HTTPException: If the two-step process fails with 422 status.
    """
    try:
        # Get vector store search results
        search_results = await vector_store.search(
            industry_descr=classification_request.org_description,
            job_title=classification_request.job_title,
            job_description=classification_request.job_description,
            correlation_id=body_id,
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

        # Get LLM instance
        llm = request.app.state.soc_llm

        # Step 1: Call unambiguous SOC code classification
        logger.info(
            f"LLM request sent for unambiguous SOC classification - "
            f"job_title: '{truncate_identifier(classification_request.job_title)}', "
            f"job_description: '{truncate_identifier(classification_request.job_description)}', "
            f"org_description: '{truncate_identifier(classification_request.org_description)}'",
            body_id=body_id,
        )
        try:
            llm_start = time.perf_counter()
            unambiguous_response, _ = await llm.unambiguous_soc_code(
                industry_descr=classification_request.org_description or "",
                semantic_search_results=short_list,
                job_title=classification_request.job_title,
                job_description=classification_request.job_description,
            )
            llm_duration_ms = int((time.perf_counter() - llm_start) * 1000)
            logger.info(
                "LLM response received for unambiguous soc prompt",
                codable=str(bool(getattr(unambiguous_response, "codable", False))),
                selected_code=(
                    str(getattr(unambiguous_response, "class_code", ""))
                    if bool(getattr(unambiguous_response, "codable", False))
                    else ""
                ),
                alt_candidates_count=str(
                    len(getattr(unambiguous_response, "alt_candidates", []) or [])
                ),
                duration_ms=str(llm_duration_ms),
                body_id=body_id,
            )
        except Exception as e:
            logger.error(
                "Error in unambiguous SOC classification", error=str(e), body_id=body_id
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "type": "classification_error",
                        "message": "The LLM could not generate a valid classification",
                        "details": f"Unambiguous classification failed: {e!s}",
                    }
                },
            ) from e

        # Check if unambiguous classification found a match
        if unambiguous_response.codable and unambiguous_response.class_code:
            candidates = [
                GenericCandidate(
                    code=c.class_code,
                    descriptive=c.class_descriptive,
                    likelihood=c.likelihood,
                )
                for c in unambiguous_response.alt_candidates
            ]
            result = GenericClassificationResult(
                type="soc",
                classified=True,
                followup=None,
                code=unambiguous_response.class_code,
                description=unambiguous_response.class_descriptive,
                candidates=candidates,
                reasoning=unambiguous_response.reasoning,
            )
        else:
            # No unambiguous match found - call formulate open question
            job_title_trunc = truncate_identifier(classification_request.job_title)
            job_desc_trunc = truncate_identifier(classification_request.job_description)
            org_desc_trunc = truncate_identifier(classification_request.org_description)
            logger.info(
                f"LLM request sent to formulate open question - "
                f"job_title: '{job_title_trunc}', "
                f"job_description: '{job_desc_trunc}', "
                f"org_description: '{org_desc_trunc}'",
                body_id=body_id,
            )
            try:
                llm_start2 = time.perf_counter()
                open_question_response, _ = await llm.formulate_open_question(
                    industry_descr=classification_request.org_description or "",
                    job_title=classification_request.job_title,
                    job_description=classification_request.job_description,
                    llm_output=unambiguous_response.alt_candidates,
                )
                llm_duration2_ms = int((time.perf_counter() - llm_start2) * 1000)
                logger.info(
                    "LLM response received for open question prompt",
                    has_followup=str(
                        bool(getattr(open_question_response, "followup", None))
                    ),
                    duration_ms=str(llm_duration2_ms),
                    body_id=body_id,
                )
            except Exception as e:
                logger.error(
                    "Error in formulate open question",
                    error=str(e),
                    body_id=body_id,
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": {
                            "type": "classification_error",
                            "message": "The LLM could not generate a valid classification",
                            "details": f"Open question formulation failed: {e!s}",
                        }
                    },
                ) from e

            # Map candidates from unambiguous response
            candidates = [
                GenericCandidate(
                    code=c.class_code,
                    descriptive=c.class_descriptive,
                    likelihood=c.likelihood,
                )
                for c in unambiguous_response.alt_candidates
            ]
            result = GenericClassificationResult(
                type="soc",
                classified=False,
                followup=open_question_response.followup,
                code=None,
                description=None,
                candidates=candidates,
                reasoning=unambiguous_response.reasoning,
            )

        # Apply rephrasing if enabled (mirrors SIC: candidates only)
        if soc_rephrase_client and candidates:
            result.candidates = _apply_soc_rephrasing(
                candidates, soc_rephrase_client, classification_request
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in SOC classification",
            error=str(e),
            body_id=body_id,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "type": "classification_error",
                    "message": "The LLM could not generate a valid classification",
                    "details": f"Response was empty or invalid JSON: {e!s}",
                }
            },
        ) from e
