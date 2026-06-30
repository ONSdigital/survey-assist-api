"""Main entry point to the Survey Assist API.

This module contains the main entry point to the Survey Assist API.
It defines the FastAPI application and the API endpoints.
"""

import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi_swagger2 import FastAPISwagger2
from industrial_classification_utils.llm.llm import ClassificationLLM
from occupational_classification_utils.llm.llm import (
    ClassificationLLM as SOCClassificationLLM,
)
from survey_assist_utils.logging import get_logger

from api.routes.v1.classify import router as classify_router
from api.routes.v1.config import router as config_router
from api.routes.v1.embeddings import router as embeddings_router
from api.routes.v1.feedback import router as feedback_router
from api.routes.v1.result import router as result_router
from api.routes.v1.sic_lookup import router as sic_lookup_router
from api.routes.v1.soc_lookup import router as soc_lookup_router
from api.services.firestore_client import init_firestore_client
from api.services.google_id_token_provider import GoogleIDTokenProvider
from api.services.sic_lookup_client import SICLookupClient
from api.services.sic_rephrase_client import SICRephraseClient
from api.services.sic_vector_store_client import SICVectorStoreClient
from api.services.soc_lookup_client import SOCLookupClient
from api.services.soc_rephrase_client import SOCRephraseClient
from api.services.soc_vector_store_client import SOCVectorStoreClient

logger = get_logger(__name__)

DEFAULT_SIC_VECTOR_STORE_URL = "http://localhost:8088"
DEFAULT_SOC_VECTOR_STORE_URL = "http://localhost:8089"


def resolve_sic_vector_store_base_url() -> str:
    """Resolve the SIC vector store base URL from environment or default."""
    env_url = os.getenv("SIC_VECTOR_STORE")
    if env_url and env_url.strip():
        logger.info(f"Using SIC vector store URL from environment: {env_url.strip()}")
        return env_url.strip()

    logger.warning(
        "SIC_VECTOR_STORE environment variable not set, using default localhost URL"
    )
    return DEFAULT_SIC_VECTOR_STORE_URL


def resolve_soc_vector_store_base_url() -> str:
    """Resolve the SOC vector store base URL from environment or default."""
    env_url = os.getenv("SOC_VECTOR_STORE")
    if env_url and env_url.strip():
        logger.info(f"Using SOC vector store URL from environment: {env_url.strip()}")
        return env_url.strip()

    logger.warning(
        "SOC_VECTOR_STORE environment variable not set, using default localhost URL"
    )
    return DEFAULT_SOC_VECTOR_STORE_URL


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage the application's lifespan.

    This function handles startup and shutdown events for the FastAPI application.
    It initialises the LLM model and client instances at startup.
    """
    # Startup
    fastapi_app.state.gemini_llm = ClassificationLLM(model_name="gemini-2.5-flash")

    # SOC classification LLM (two-step: unambiguous_soc_code, then formulate_open_question)
    fastapi_app.state.soc_llm = SOCClassificationLLM(model_name="gemini-2.5-flash")

    # Initialise Firestore client (if configured)
    init_firestore_client()

    # Create SIC lookup client
    sic_lookup_data_path = os.getenv("SIC_LOOKUP_DATA_PATH")
    if sic_lookup_data_path and sic_lookup_data_path.strip():
        fastapi_app.state.sic_lookup_client = SICLookupClient(
            data_path=sic_lookup_data_path.strip()
        )
    else:
        fastapi_app.state.sic_lookup_client = SICLookupClient()

    # Create SOC lookup client
    soc_lookup_data_path = os.getenv("SOC_LOOKUP_DATA_PATH")
    if soc_lookup_data_path and soc_lookup_data_path.strip():
        fastapi_app.state.soc_lookup_client = SOCLookupClient(
            data_path=soc_lookup_data_path.strip()
        )
    else:
        fastapi_app.state.soc_lookup_client = SOCLookupClient()

    # Create SIC rephrase client
    sic_rephrase_data_path = os.getenv("SIC_REPHRASE_DATA_PATH")
    if sic_rephrase_data_path and sic_rephrase_data_path.strip():
        fastapi_app.state.sic_rephrase_client = SICRephraseClient(
            data_path=sic_rephrase_data_path.strip()
        )
    else:
        fastapi_app.state.sic_rephrase_client = SICRephraseClient()

    # Create SOC rephrase client
    soc_rephrase_data_path = os.getenv("SOC_REPHRASE_DATA_PATH")
    if soc_rephrase_data_path and soc_rephrase_data_path.strip():
        fastapi_app.state.soc_rephrase_client = SOCRephraseClient(
            data_path=soc_rephrase_data_path.strip()
        )
    else:
        fastapi_app.state.soc_rephrase_client = SOCRephraseClient()

    # Create shared async HTTP client for vector store services
    shared_http_client = httpx.AsyncClient()
    fastapi_app.state.vector_store_http_client = shared_http_client

    sic_url = resolve_sic_vector_store_base_url()
    soc_url = resolve_soc_vector_store_base_url()

    # Create Google ID token providers for SIC and SOC vector store services
    sic_token_provider = GoogleIDTokenProvider(sic_url)
    soc_token_provider = GoogleIDTokenProvider(soc_url)

    # Create SIC and SOC vector store clients with shared HTTP client and
    # separate token providers
    fastapi_app.state.sic_vector_store_client = SICVectorStoreClient(
        base_url=sic_url,
        http_client=shared_http_client,
        google_id_token_provider=sic_token_provider,
    )

    fastapi_app.state.soc_vector_store_client = SOCVectorStoreClient(
        base_url=soc_url,
        http_client=shared_http_client,
        google_id_token_provider=soc_token_provider,
    )

    logger.info(
        "Application clients initialised",
        sic_llm=type(fastapi_app.state.gemini_llm).__name__,
        soc_llm=type(fastapi_app.state.soc_llm).__name__,
        sic_lookup=type(fastapi_app.state.sic_lookup_client).__name__,
        soc_lookup=type(fastapi_app.state.soc_lookup_client).__name__,
        sic_rephrase=type(fastapi_app.state.sic_rephrase_client).__name__,
        soc_rephrase=type(fastapi_app.state.soc_rephrase_client).__name__,
        vector_store_http_client_shared=str(
            fastapi_app.state.sic_vector_store_client.http_client
            is fastapi_app.state.soc_vector_store_client.http_client
        ),
    )

    try:
        yield
    finally:
        # Shutdown
        await shared_http_client.aclose()


app: FastAPI = FastAPI(
    title="Survey Assist API",
    description="API for interacting with backend data processing services such as classification",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable Swagger2 endpoints (replaces OpenAPI v3)
FastAPISwagger2(app)  # type: ignore

# Include versioned routes
app.include_router(config_router, prefix="/v1/survey-assist")
app.include_router(embeddings_router, prefix="/v1/survey-assist")
app.include_router(sic_lookup_router, prefix="/v1/survey-assist")
app.include_router(soc_lookup_router, prefix="/v1/survey-assist")
app.include_router(classify_router, prefix="/v1/survey-assist")
app.include_router(result_router, prefix="/v1/survey-assist")
app.include_router(feedback_router, prefix="/v1/survey-assist")


@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    """Root endpoint for the Survey Assist API.

    Returns:
        dict: A dictionary with a message indicating the API is running.
    """
    return {"message": "Survey Assist API is running"}
