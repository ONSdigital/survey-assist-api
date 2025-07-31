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


class ClassificationOptions(BaseModel):
    """Model for classification options.

    Attributes:
        sic (Optional[SICOptions]): SIC-specific classification options.
        soc (Optional[SOCOptions]): SOC-specific classification options.
    """

    sic: Optional["SICOptions"] = Field(
        None, description="SIC-specific classification options"
    )
    soc: Optional["SOCOptions"] = Field(
        None, description="SOC-specific classification options"
    )


class SICOptions(BaseModel):
    """Model for SIC-specific classification options.

    Attributes:
        rephrased (bool): Whether to apply rephrasing to SIC classification results.
            Defaults to True to maintain backward compatibility.
    """

    rephrased: bool = Field(
        default=True,
        description="Whether to apply rephrasing to SIC classification results",
    )


class SOCOptions(BaseModel):
    """Model for SOC-specific classification options.

    Attributes:
        rephrased (bool): Whether to apply rephrasing to SOC classification results.
            Defaults to True to maintain backward compatibility.
    """

    rephrased: bool = Field(
        default=True,
        description="Whether to apply rephrasing to SOC classification results",
    )


class ClassificationRequest(BaseModel):
    """Model for the classification request.

    Attributes:
        llm (LLMModel): The LLM model to use.
        type (ClassificationType): Type of classification.
        job_title (str): Survey response for Job Title.
        job_description (str): Survey response for Job Description.
        org_description (Optional[str]): Survey response for Organisation / Industry Description.
        options (Optional[ClassificationOptions]): Optional classification options.
    """

    llm: LLMModel
    type: ClassificationType
    job_title: str = Field(..., description="Survey response for Job Title")
    job_description: str = Field(..., description="Survey response for Job Description")
    org_description: Optional[str] = Field(
        None, description="Survey response for Organisation / Industry Description"
    )
    options: Optional[ClassificationOptions] = Field(
        None, description="Optional classification options"
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
    likelihood: float = Field(ge=0.0, le=1.0, description="Likelihood of match")


class ClassificationResponse(BaseModel):
    """Model for the classification response.

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


# New generic models for supporting both SIC and SOC classification
class GenericCandidate(BaseModel):
    """Model for a generic classification candidate.

    Attributes:
        code (str): The classification code.
        descriptive (str): The classification description.
        likelihood (float): The likelihood of the match.
    """

    code: str = Field(..., description="Classification code")
    descriptive: str = Field(..., description="Classification description")
    likelihood: float = Field(ge=0.0, le=1.0, description="Likelihood of match")


class GenericClassificationResult(BaseModel):
    """Model for a generic classification result.

    Attributes:
        type (str): The type of classification (sic, soc).
        classified (bool): Whether the input could be definitively classified.
        followup (Optional[str]): Additional question to help classify.
        code (Optional[str]): The classification code. Empty if classified=False.
        description (Optional[str]): The classification description. Empty if classified=False.
        candidates (list[GenericCandidate]): List of potential classification candidates.
        reasoning (str): Reasoning behind the LLM's response.
    """

    type: str = Field(..., description="Type of classification (sic, soc)")
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
        None, description="Classification description. Empty if classified=False"
    )
    candidates: list[GenericCandidate] = Field(
        ..., description="List of potential classification candidates"
    )
    reasoning: str = Field(..., description="Reasoning behind the LLM's response")


class GenericClassificationResponse(BaseModel):
    """Model for the generic classification response.

    Attributes:
        requested_type (str): The type of classification that was requested.
        results (list[GenericClassificationResult]): List of classification results.
    """

    requested_type: str = Field(
        ..., description="Type of classification that was requested"
    )
    results: list[GenericClassificationResult] = Field(
        ..., description="List of classification results"
    )
