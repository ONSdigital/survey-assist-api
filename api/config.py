"""Configuration settings for the Survey Assist API."""

import logging
import os

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Prompt version constants
# These identifiers match the version keys used in the config endpoint response
# (see api/models/config.py ConfigResponse and api/routes/v1/config.py)
PROMPT_VERSION_V1V2 = "v1v2"  # Original single-prompt approach using sa_rag_sic_code
PROMPT_VERSION_V3 = "v3"  # Two-step using unambiguous + follow-up prompts
DEFAULT_PROMPT_VERSION = PROMPT_VERSION_V1V2  # Original single prompt
VALID_PROMPT_VERSIONS = [PROMPT_VERSION_V1V2, PROMPT_VERSION_V3]


# pylint: disable=too-few-public-methods
class Settings(BaseSettings):
    """Settings for the Survey Assist API."""

    GCP_PROJECT_ID: str | None = os.getenv("GCP_PROJECT_ID")
    FIRESTORE_DB_ID: str | None = os.getenv("FIRESTORE_DB_ID")

    # Data file paths - defaults to example datasets from sic-classification-library package
    SIC_LOOKUP_DATA_PATH: str | None = os.getenv("SIC_LOOKUP_DATA_PATH")
    SIC_REPHRASE_DATA_PATH: str | None = os.getenv("SIC_REPHRASE_DATA_PATH")

    # Prompt version configuration
    DEFAULT_PROMPT_VERSION: str = os.getenv("DEFAULT_PROMPT_VERSION", "v1v2")

    def __post_init__(self):
        """Post-initialisation hook to log warnings about missing environment variables."""
        if not self.GCP_PROJECT_ID:
            logger.warning(
                "GCP_PROJECT_ID not set - default project discovery will be used if available"
            )
        if not self.FIRESTORE_DB_ID:
            logger.warning(
                "FIRESTORE_DB_ID not set - Firestore features will be disabled until set"
            )
        if not self.SIC_LOOKUP_DATA_PATH:
            logger.warning(
                "SIC_LOOKUP_DATA_PATH not set - will use default example dataset "
                "from sic-classification-library package"
            )
        if not self.SIC_REPHRASE_DATA_PATH:
            logger.warning(
                "SIC_REPHRASE_DATA_PATH not set - will use default example dataset "
                "from sic-classification-library package"
            )

    def as_dict(self) -> dict:
        """Return all settings as a dictionary."""
        return self.model_dump()

    class Config:
        """Pydantic config."""

        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
