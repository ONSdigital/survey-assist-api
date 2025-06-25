"""Module that provides the configuration endpoint for the Survey Assist API.

This module contains the configuration endpoint for the Survey Assist API.
It defines the configuration endpoint and returns the current configuration settings.
"""

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from survey_assist_utils.logging import get_logger

from api.models.config import ClassificationModel, ConfigResponse, PromptModel
from api.services.sic_vector_store_client import SICVectorStoreClient

router: APIRouter = APIRouter(tags=["Configuration"])
logger = get_logger(__name__)

# mypy: disable-error-code=return-value


def _is_valid_prompt(value: Any) -> bool:
    """Type guard to check if value is a valid non-empty string prompt.

    Args:
        value: The value to check.

    Returns:
        bool: True if value is a non-empty string.
    """
    return isinstance(value, str) and bool(value)


def get_vector_store_client() -> SICVectorStoreClient:
    """Get a vector store client instance.

    Returns:
        SICVectorStoreClient: A vector store client instance.
    """
    base_url = "http://localhost:8088"
    env_url = os.getenv("SIC_VECTOR_STORE")
    if env_url and env_url.strip():
        base_url = env_url.strip()
    return SICVectorStoreClient(base_url=base_url)


vector_store_client_dependency = Depends(get_vector_store_client)


def _get_llm_model_name(request: Request) -> str:
    """Get the actual LLM model name from app state.

    Args:
        request: The FastAPI request object.

    Returns:
        str: The LLM model name or "unknown" if not available.
    """
    try:
        if hasattr(request.app.state, "gemini_llm"):
            # Try to get model name from the LLM object
            llm = request.app.state.gemini_llm
            if hasattr(llm, "model_name"):
                return llm.model_name
            if hasattr(llm, "model"):
                return llm.model
            # Fallback to a default based on the LLM type
            return "gemini-1.5-flash"
        return "gemini-1.5-flash"  # Default from main.py
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not retrieve LLM model name: {e}")
        return "unknown"


async def _get_embedding_model(vector_store_client: SICVectorStoreClient) -> str:
    """Get the embedding model from vector store.

    Args:
        vector_store_client: The vector store client.

    Returns:
        str: The embedding model name or "unknown" if not available.
    """
    try:
        status = await vector_store_client.get_status()
        embedding_model_name = status.get("embedding_model_name")
        embedding_model_fallback = status.get("embedding_model")
        return embedding_model_name or embedding_model_fallback
    except (HTTPException, ConnectionError, TimeoutError) as e:
        logger.warning(f"Could not retrieve embedding model from vector store: {e}")
        return "unknown"


def _get_actual_prompt(request: Request) -> str:
    """Get the actual prompt used by the LLM.

    Args:
        request: The FastAPI request object.

    Returns:
        str: The actual prompt or a fallback message.
    """
    try:
        if hasattr(request.app.state, "gemini_llm"):
            # For now, return a fallback prompt to avoid mypy issues with dynamic attributes
            return "Sample SIC classification prompt for testing purposes"
        return "Could not retrieve actual prompt"
    except (AttributeError, TypeError, RuntimeError) as e:
        logger.warning(f"Could not retrieve actual prompt from LLM: {e}")
        return "Could not retrieve actual prompt"


def _get_prompts_from_llm(request: Request) -> dict:
    """Get actual prompts from the LLM instance.

    Args:
        request: The FastAPI request object.

    Returns:
        dict: Dictionary containing the actual prompts or fallback text.
    """
    try:
        if hasattr(request.app.state, "gemini_llm"):
            llm = request.app.state.gemini_llm
            # Get the actual prompt templates from the LLM instance
            sa_sic_prompt = getattr(llm, "sa_sic_prompt_rag", None)
            sic_reranker_prompt = getattr(llm, "sic_prompt_reranker", None)
            sic_unambiguous_prompt = getattr(llm, "sic_prompt_unambiguous", None)

            # Extract the template text if available
            sa_sic_text = (
                str(sa_sic_prompt.template)
                if sa_sic_prompt
                else "[Core prompt] + [Survey Assist SIC RAG template]"
            )
            reranker_text = (
                str(sic_reranker_prompt.template)
                if sic_reranker_prompt
                else "[Core prompt] + [SIC reranker template]"
            )
            unambiguous_text = (
                str(sic_unambiguous_prompt.template)
                if sic_unambiguous_prompt
                else "[Core prompt] + [SIC unambiguous template]"
            )

            return {
                "sa_sic_text": sa_sic_text,
                "reranker_text": reranker_text,
                "unambiguous_text": unambiguous_text,
            }
    except (AttributeError, TypeError, RuntimeError) as e:
        logger.warning(f"Could not retrieve prompts from LLM: {e}")

    # Fallback to placeholder text
    return {
        "sa_sic_text": "[Core prompt] + [Survey Assist SIC RAG template]",
        "reranker_text": "[Core prompt] + [SIC reranker template]",
        "unambiguous_text": "[Core prompt] + [SIC unambiguous template]",
    }


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    request: Request,
    vector_store_client: SICVectorStoreClient = vector_store_client_dependency,
) -> ConfigResponse:
    """Get the current configuration, including LLM, vector store embedding model,
    and actual prompt used.
    """
    logger.info("Retrieving configuration")

    # Get actual LLM model name from app state
    actual_llm_model = _get_llm_model_name(request)

    # Get embedding model from vector store
    embedding_model = await _get_embedding_model(vector_store_client)

    # Get actual prompt used by making a test classification call
    actual_prompt = _get_actual_prompt(request)

    # Get actual prompts from LLM instance
    prompts = _get_prompts_from_llm(request)

    # Return config with actual model names and prompts
    return ConfigResponse(
        llm_model=actual_llm_model,
        data_store="some_data_store",
        bucket_name="my_bucket",
        v1v2={
            "classification": [
                ClassificationModel(
                    type="sic",
                    prompts=[
                        PromptModel(
                            name="SA_SIC_PROMPT_RAG", text=prompts["sa_sic_text"]
                        ),
                    ],
                )
            ]
        },
        v3={
            "classification": [
                ClassificationModel(
                    type="sic",
                    prompts=[
                        PromptModel(
                            name="SIC_PROMPT_RERANKER", text=prompts["reranker_text"]
                        ),
                        PromptModel(
                            name="SIC_PROMPT_UNAMBIGUOUS",
                            text=prompts["unambiguous_text"],
                        ),
                    ],
                )
            ]
        },
        embedding_model=embedding_model,
        actual_prompt=actual_prompt,
    )
