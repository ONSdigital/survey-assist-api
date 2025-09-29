"""Main entry point to the Survey Assist API.

This module contains the main entry point to the Survey Assist API.
It defines the FastAPI application and the API endpoints.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_swagger2 import FastAPISwagger2
from industrial_classification_utils.llm.llm import ClassificationLLM

from api.routes.v1.classify import router as classify_router
from api.routes.v1.config import router as config_router
from api.routes.v1.embeddings import router as embeddings_router
from api.routes.v1.result import router as result_router
from api.routes.v1.sic_lookup import router as sic_lookup_router
from api.services.sic_lookup_client import SICLookupClient
from api.services.sic_rephrase_client import SICRephraseClient


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage the application's lifespan.

    This function handles startup and shutdown events for the FastAPI application.
    It initialises the LLM model and client instances at startup.
    """
    # Startup
    fastapi_app.state.gemini_llm = ClassificationLLM(model_name="gemini-2.5-flash")

    # Create SIC lookup client
    sic_lookup_data_path = os.getenv("SIC_LOOKUP_DATA_PATH")
    if sic_lookup_data_path and sic_lookup_data_path.strip():
        fastapi_app.state.sic_lookup_client = SICLookupClient(
            data_path=sic_lookup_data_path.strip()
        )
    else:
        fastapi_app.state.sic_lookup_client = SICLookupClient()

    # Create SIC rephrase client
    sic_rephrase_data_path = os.getenv("SIC_REPHRASE_DATA_PATH")
    if sic_rephrase_data_path and sic_rephrase_data_path.strip():
        fastapi_app.state.sic_rephrase_client = SICRephraseClient(
            data_path=sic_rephrase_data_path.strip()
        )
    else:
        fastapi_app.state.sic_rephrase_client = SICRephraseClient()

    yield
    # Shutdown
    # Add any cleanup code here if needed


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
app.include_router(classify_router, prefix="/v1/survey-assist")
app.include_router(result_router, prefix="/v1/survey-assist")


@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    """Root endpoint for the Survey Assist API.

    Returns:
        dict: A dictionary with a message indicating the API is running.
    """
    return {"message": "Survey Assist API is running"}
