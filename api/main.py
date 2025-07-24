"""Main entry point to the Survey Assist API.

This module contains the main entry point to the Survey Assist API.
It defines the FastAPI application and the API endpoints.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from industrial_classification_utils.llm.llm import ClassificationLLM

from api.routes.v1.classify import router as classify_router
from api.routes.v1.config import router as config_router
from api.routes.v1.embeddings import router as embeddings_router
from api.routes.v1.result import router as result_router
from api.routes.v1.sic_lookup import router as sic_lookup_router
from occupational_classification_utils.llm.llm import (
    ClassificationLLM as SOCLLM,  # type: ignore # mypy: disable-error-code="import-not-found"  # pylint: disable=line-too-long
)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Manage the application's lifespan.

    This function handles startup and shutdown events for the FastAPI application.
    It initialises the LLM model at startup.
    """
    # Startup
    fastapi_app.state.gemini_llm = ClassificationLLM(model_name="gemini-1.5-flash")
    fastapi_app.state.soc_llm = SOCLLM(model_name="gemini-1.5-flash")
    yield
    # Shutdown
    # Add any cleanup code here if needed


app: FastAPI = FastAPI(
    title="Survey Assist API",
    description="API for interacting with backend data processing services such as classification",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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
