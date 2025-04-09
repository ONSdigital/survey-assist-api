"""Main entry point to the Survey Assist API.

This module contains the main entry point to the Survey Assist API.
It defines the FastAPI application and the API endpoints.
"""

from fastapi import FastAPI

from api.routes.v1.config import router as config_router
from api.routes.v1.sic_lookup import router as sic_lookup_router

app: FastAPI = FastAPI(
    title="LLM API",
    description="API for interacting with LLM",
    version="1.0",
)

# Include versioned routes
app.include_router(config_router, prefix="/v1/survey-assist")


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint for the Survey Assist API.

    Returns:
        dict: A dictionary with a message indicating the API is running.
    """
    return {"message": "Survey Assist API is running"}
