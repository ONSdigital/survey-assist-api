"""Main entry point to the Survey Assist API.

This module contains the main entry point to the Survey Assist API.
It defines the FastAPI application and the API endpoints.
"""

from fastapi import FastAPI
from api.routes.v1.config import router as config_router
from api.routes.v1.sic_lookup import router as sic_lookup_router

app: FastAPI = FastAPI(
    title="Survey Assist API",
    description="API for interacting with backend data processing services such as classification",
    version="1.0.0",
    contact={
        "name": "ONS Digital",
        "email": "steve.gibbard@ons.gov.uk"
    },
    openapi_url="/v1/survey-assist/openapi.json",
    docs_url="/v1/survey-assist/docs",
    redoc_url="/v1/survey-assist/redoc",
)

# Include versioned routes
app.include_router(config_router, prefix="/v1/survey-assist")
app.include_router(sic_lookup_router, prefix="/v1/survey-assist")

@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    """Root endpoint for the Survey Assist API.

    Returns:
        dict: A dictionary with a message indicating the API is running.
    """
    return {"message": "Survey Assist API is running"}
