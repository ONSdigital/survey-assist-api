"""Configuration settings for the Survey Assist API."""

import os

from pydantic_settings import BaseSettings


# pylint: disable=too-few-public-methods
class Settings(BaseSettings):
    """Settings for the Survey Assist API."""

    GCP_BUCKET_NAME: str = os.getenv("GCP_BUCKET_NAME", "sandbox-survey-assist")

    # Data file paths
    SIC_LOOKUP_DATA_PATH: str = os.getenv(
        "SIC_LOOKUP_DATA_PATH", "data/sic_knowledge_base_utf8.csv"
    )
    SIC_REPHRASE_DATA_PATH: str = os.getenv(
        "SIC_REPHRASE_DATA_PATH", "data/sic_rephrased_descriptions_2025_02_03.csv"
    )

    def as_dict(self) -> dict:
        """Return all settings as a dictionary."""
        return self.model_dump()

    class Config:
        """Pydantic config."""

        env_file = ".env"


settings = Settings()
