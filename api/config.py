"""Configuration settings for the Survey Assist API."""

import os

from pydantic_settings import BaseSettings


# pylint: disable=too-few-public-methods
class Settings(BaseSettings):
    """Settings for the Survey Assist API."""

    GCP_BUCKET_NAME: str = os.getenv("GCP_BUCKET_NAME", "sandbox-survey-assist")

    def as_dict(self) -> dict:
        """Return all settings as a dictionary."""
        return self.model_dump()

    class Config:
        """Pydantic config."""

        env_file = ".env"


settings = Settings()
