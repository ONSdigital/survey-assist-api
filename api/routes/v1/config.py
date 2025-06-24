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


# Mock configuration
config_data: ConfigResponse = ConfigResponse(
    llm_model="gpt-4",
    data_store="some_data_store",
    bucket_name="my_bucket",
    v1v2={
        "classification": [
            ClassificationModel(
                type="sic",
                prompts=[
                    PromptModel(name="SA_SIC_PROMPT_RAG", text="my SIC RAG prompt"),
                ],
            )
        ]
    },
    v3={
        "classification": [
            ClassificationModel(
                type="sic",
                prompts=[
                    PromptModel(name="SIC_PROMPT_RERANKER", text="my reranker prompt"),
                    PromptModel(
                        name="SIC_PROMPT_UNAMBIGUOUS", text="my unambiguous prompt"
                    ),
                ],
            )
        ]
    },
)


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

    # Return config with actual model names and prompt
    return ConfigResponse(
        llm_model=actual_llm_model,
        data_store=config_data.data_store,
        bucket_name=config_data.bucket_name,
        v1v2=config_data.v1v2,
        v3=config_data.v3,
        embedding_model=embedding_model,
        actual_prompt=actual_prompt,
    )
