"""Module that provides the models for the classification endpoint.

This module contains the request and response models for the classification endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ClassificationRequest(BaseModel):
    """Model for the classification request.

    Attributes:
        llm (str): The LLM model to use (gemini or chat-gpt).
        type (str): Type of classification (sic, soc or sic_soc).
        job_title (str): Survey response for Job Title.
        job_description (str): Survey response for Job Description.
        org_description (str): Survey response for Organisation / Industry Description.
    """

    llm: str = Field(..., description="LLM Model (gemini or chat-gpt)")
    type: str = Field(..., description="Type of classification (sic, soc or sic_soc)")
    job_title: str = Field(..., description="Survey response for Job Title")
    job_description: str = Field(..., description="Survey response for Job Description")
    org_description: str = Field(
        ..., description="Survey response for Organisation / Industry Description"
    )


class SicCandidate(BaseModel):
    """Model for a SIC code candidate.

    Attributes:
        sic_code (str): The SIC code.
        sic_descriptive (str): The SIC code description.
        likelihood (float): The likelihood of the match.
    """

    sic_code: str = Field(..., description="SIC code")
    sic_descriptive: str = Field(..., description="SIC code description")
    likelihood: float = Field(..., description="Likelihood of match")


class ClassificationResponse(BaseModel):
    """Model for the classification response.

    Attributes:
        classified (bool): Whether the input could be definitively classified.
        followup (Optional[str]): Additional question to help classify.
        sic_code (Optional[str]): The SIC code.
        sic_description (Optional[str]): The SIC code description.
        sic_candidates (List[SicCandidate]): List of potential SIC code candidates.
        reasoning (Optional[str]): Reasoning behind the LLM's response.
    """

    classified: bool = Field(..., description="Could the input be definitively classified?")
    followup: Optional[str] = Field(None, description="Additional question to help classify")
    sic_code: Optional[str] = Field(None, description="SIC code")
    sic_description: Optional[str] = Field(None, description="SIC code description")
    sic_candidates: List[SicCandidate] = Field(
        ..., description="List of potential SIC code candidates"
    )
    reasoning: Optional[str] = Field(None, description="Reasoning behind the LLM's response") 