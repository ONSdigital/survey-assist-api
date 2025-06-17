"""Configuration settings for the Survey Assist API."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the Survey Assist API."""
    
    GCP_BUCKET_NAME: str = os.getenv("GCP_BUCKET_NAME", "sandbox-survey-assist")

    class Config:
        """Pydantic config."""
        env_file = ".env"


settings = Settings() 