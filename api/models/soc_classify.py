"""Module that provides the models for SOC classification endpoint.

This module contains the request and response models for the SOC classification endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from typing import Optional

from pydantic import BaseModel, Field


class SocCandidate(BaseModel):
    """Model for a SOC code candidate.

    Attributes:
        soc_code (str): The SOC code.
        soc_descriptive (str): The SOC code description.
        likelihood (float): The likelihood of the match.
    """

    soc_code: str = Field(..., description="SOC code")
    soc_descriptive: str = Field(..., description="SOC code description")
    likelihood: float = Field(ge=0.0, le=1.0, description="Likelihood of match")


class SocClassificationResponse(BaseModel):
    """Model for the SOC classification response.

    Attributes:
        classified (bool): Whether the input could be definitively classified.
        followup (Optional[str]): Additional question to help classify.
        soc_code (Optional[str]): The SOC code. Empty if classified=False.
        soc_description (Optional[str]): The SOC code description. Empty if classified=False.
        soc_candidates (list[SocCandidate]): List of potential SOC code candidates.
        reasoning (str): Reasoning behind the LLM's response.
        prompt_used (Optional[str]): The actual prompt that was sent to the LLM.
    """

    classified: bool = Field(
        ..., description="Could the input be definitively classified?"
    )
    followup: Optional[str] = Field(
        None, description="Additional question to help classify"
    )
    soc_code: Optional[str] = Field(
        None, description="SOC code. Empty if classified=False"
    )
    soc_description: Optional[str] = Field(
        None, description="SOC code description. Empty if classified=False"
    )
    soc_candidates: list[SocCandidate] = Field(
        ..., description="List of potential SOC code candidates"
    )
    reasoning: str = Field(..., description="Reasoning behind the LLM's response")
    prompt_used: Optional[str] = Field(
        None, description="The actual prompt that was sent to the LLM"
    )
