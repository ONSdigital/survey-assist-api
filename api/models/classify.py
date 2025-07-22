"""Module that provides the models for the classification endpoint.

This module contains the request and response models for the classification endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMModel(str, Enum):
    """Enum for LLM models."""

    CHAT_GPT = "chat-gpt"
    GEMINI = "gemini"


class ClassificationType(str, Enum):
    """Enum for classification types."""

    SIC = "sic"
    SOC = "soc"
    SIC_SOC = "sic_soc"


class ClassificationRequest(BaseModel):
    """Model for the classification request.

    Attributes:
        llm (LLMModel): The LLM model to use.
        type (ClassificationType): Type of classification.
        job_title (str): Survey response for Job Title.
        job_description (str): Survey response for Job Description.
        org_description (Optional[str]): Survey response for Organisation / Industry Description.
    """

    llm: LLMModel
    type: ClassificationType
    job_title: str = Field(..., description="Survey response for Job Title")
    job_description: str = Field(..., description="Survey response for Job Description")
    org_description: Optional[str] = Field(
        None, description="Survey response for Organisation / Industry Description"
    )


class Candidate(BaseModel):
    """Generic model for a classification code candidate.

    Attributes:
        code (str): The classification code (SIC or SOC).
        descriptive (str): The code description.
        likelihood (float): The likelihood of the match.
    """

    code: str = Field(..., description="Classification code")
    descriptive: str = Field(..., description="Code description")
    likelihood: float = Field(ge=0.0, le=1.0, description="Likelihood of match")


class ClassificationResult(BaseModel):
    """Generic model for a classification result.

    Attributes:
        type (str): The type of classification (sic or soc).
        classified (bool): Whether the input could be definitively classified.
        followup (Optional[str]): Additional question to help classify.
        code (Optional[str]): The classification code. Empty if classified=False.
        description (Optional[str]): The code description. Empty if classified=False.
        candidates (list[Candidate]): List of potential code candidates.
        reasoning (str): Reasoning behind the LLM's response.
    """

    type: str = Field(..., description="Type of classification (sic or soc)")
    classified: bool = Field(
        ..., description="Could the input be definitively classified?"
    )
    followup: Optional[str] = Field(
        None, description="Additional question to help classify"
    )
    code: Optional[str] = Field(
        None, description="Classification code. Empty if classified=False"
    )
    description: Optional[str] = Field(
        None, description="Code description. Empty if classified=False"
    )
    candidates: list[Candidate] = Field(
        ..., description="List of potential code candidates"
    )
    reasoning: str = Field(..., description="Reasoning behind the LLM's response")


class ClassificationResponse(BaseModel):
    """Model for the classification response.

    Attributes:
        requested_type (str): The requested classification type.
        results (list[ClassificationResult]): List of classification results.
    """

    requested_type: str = Field(..., description="The requested classification type")
    results: list[ClassificationResult] = Field(
        ..., description="List of classification results"
    )


# Legacy models for backward compatibility
class SicCandidate(BaseModel):
    """Model for a SIC code candidate.

    Attributes:
        sic_code (str): The SIC code.
        sic_descriptive (str): The SIC code description.
        likelihood (float): The likelihood of the match.
    """

    sic_code: str = Field(..., description="SIC code")
    sic_descriptive: str = Field(..., description="SIC code description")
    likelihood: float = Field(ge=0.0, le=1.0, description="Likelihood of match")


class LegacyClassificationResponse(BaseModel):
    """Legacy model for the classification response.

    Attributes:
        classified (bool): Whether the input could be definitively classified.
        followup (Optional[str]): Additional question to help classify.
        sic_code (Optional[str]): The SIC code. Empty if classified=False.
        sic_description (Optional[str]): The SIC code description. Empty if classified=False.
        sic_candidates (list[SicCandidate]): List of potential SIC code candidates.
        reasoning (str): Reasoning behind the LLM's response.
        prompt_used (Optional[str]): The actual prompt that was sent to the LLM.
    """

    classified: bool = Field(
        ..., description="Could the input be definitively classified?"
    )
    followup: Optional[str] = Field(
        None, description="Additional question to help classify"
    )
    sic_code: Optional[str] = Field(
        None, description="SIC code. Empty if classified=False"
    )
    sic_description: Optional[str] = Field(
        None, description="SIC code description. Empty if classified=False"
    )
    sic_candidates: list[SicCandidate] = Field(
        ..., description="List of potential SIC code candidates"
    )
    reasoning: str = Field(..., description="Reasoning behind the LLM's response")
    prompt_used: Optional[str] = Field(
        None, description="The actual prompt that was sent to the LLM"
    )
