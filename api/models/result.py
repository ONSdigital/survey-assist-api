"""Module that provides the models for the result endpoint.

This module contains the request and response models for the result endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class InputField(BaseModel):
    """Model for input field data."""
    field: str = Field(..., description="The field name")
    value: str = Field(..., description="The field value")


class FollowUpQuestion(BaseModel):
    """Model for follow-up questions."""
    id: str = Field(..., description="Question identifier")
    text: str = Field(..., description="Question text")
    type: str = Field(..., description="Question type (text or select)", pattern="^(text|select)$")
    select_options: Optional[List[str]] = Field(None, description="Options for select type questions")
    response: str = Field(..., description="User's response to the question")


class FollowUp(BaseModel):
    """Model for follow-up data."""
    questions: List[FollowUpQuestion] = Field(..., description="List of follow-up questions")


class Candidate(BaseModel):
    """Model for classification candidates."""
    code: str = Field(..., description="The classification code")
    description: str = Field(..., description="The classification description")
    likelihood: float = Field(..., description="Confidence score between 0 and 1")


class ClassificationResponse(BaseModel):
    """Model for classification response."""
    classified: bool = Field(..., description="Whether the input was classified")
    code: str = Field(..., description="The classification code")
    description: str = Field(..., description="The classification description")
    reasoning: str = Field(..., description="Reasoning behind the classification")
    candidates: List[Candidate] = Field(..., description="List of potential classifications")
    follow_up: FollowUp = Field(..., description="Follow-up questions if needed")


class PotentialDivision(BaseModel):
    """Model for potential division data."""
    code: str = Field(..., description="The division code")
    title: str = Field(..., description="The division title")
    detail: Optional[str] = Field(None, description="Additional division details")


class PotentialCode(BaseModel):
    """Model for potential code data."""
    code: str = Field(..., description="The code")
    description: str = Field(..., description="The code description")


class LookupResponse(BaseModel):
    """Model for lookup response."""
    found: bool = Field(..., description="Whether matches were found")
    potential_codes_count: int = Field(..., description="Number of potential codes found")
    potential_divisions: List[PotentialDivision] = Field(..., description="List of potential divisions")
    potential_codes: List[PotentialCode] = Field(..., description="List of potential codes")


class SurveyAssistInteraction(BaseModel):
    """Model for survey assist interaction."""
    type: str = Field(..., description="Interaction type (classify or lookup)", pattern="^(classify|lookup)$")
    flavour: str = Field(..., description="Classification flavour (sic or soc)", pattern="^(sic|soc)$")
    time_start: datetime = Field(..., description="Start time of the interaction")
    time_end: datetime = Field(..., description="End time of the interaction")
    input: List[InputField] = Field(..., description="Input data for the interaction")
    response: Union[ClassificationResponse, LookupResponse] = Field(..., description="Response from the interaction")


class Response(BaseModel):
    """Model for a single response."""
    person_id: str = Field(..., description="Identifier for the person")
    time_start: datetime = Field(..., description="Start time of the response")
    time_end: datetime = Field(..., description="End time of the response")
    survey_assist_interactions: List[SurveyAssistInteraction] = Field(..., description="List of survey assist interactions")


class SurveyAssistResult(BaseModel):
    """Model for the complete survey assist result."""
    survey_id: str = Field(..., description="Identifier for the survey")
    case_id: str = Field(..., description="Identifier for the case")
    time_start: datetime = Field(..., description="Start time of the survey")
    time_end: datetime = Field(..., description="End time of the survey")
    responses: List[Response] = Field(..., description="List of responses")


class ResultResponse(BaseModel):
    """Response model for result endpoints."""
    message: str = Field(..., description="Response message")
    result_id: Optional[str] = Field(None, description="Unique identifier for the stored result")
