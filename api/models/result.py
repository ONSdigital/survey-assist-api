"""Module that provides the models for the result endpoint.

This module contains the request and response models for the result endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


class InputField(BaseModel):
    """Model for input field data."""

    field: str = Field(..., description="The field name")
    value: str = Field(..., description="The field value")


class FollowUpQuestion(BaseModel):
    """Model for follow-up questions."""

    id: str = Field(..., description="Question identifier")
    text: str = Field(..., description="Question text")
    type: str = Field(
        ...,
        description="Question type (text, textarea or select)",
        pattern="^(text|textarea|select)$",
    )
    select_options: Optional[list[str]] = Field(
        None, description="Options for select type questions"
    )
    response: str = Field(..., description="User's response to the question")


class FollowUp(BaseModel):
    """Model for follow-up data."""

    questions: list[FollowUpQuestion] = Field(
        ..., description="List of follow-up questions"
    )


class Candidate(BaseModel):
    """Model for classification candidates."""

    code: str = Field(..., description="The classification code")
    description: str = Field(..., description="The classification description")
    likelihood: float = Field(..., description="Confidence score between 0 and 1")


class GenericCandidate(BaseModel):
    """Model for generic classification candidates that can be SIC or SOC."""

    code: str = Field(..., description="The classification code")
    descriptive: str = Field(..., description="The classification description")
    likelihood: float = Field(..., description="Confidence score between 0 and 1")


class ClassificationResponse(BaseModel):
    """Model for classification response."""

    classified: bool = Field(..., description="Whether the input was classified")
    code: Optional[str] = Field(None, description="The classification code")
    description: Optional[str] = Field(
        None, description="The classification description"
    )
    reasoning: str = Field(..., description="Reasoning behind the classification")
    candidates: list[Candidate] = Field(
        ..., description="List of potential classifications"
    )
    follow_up: FollowUp = Field(..., description="Follow-up questions if needed")


class GenericClassificationResult(BaseModel):
    """Model for generic classification result that can be SIC or SOC."""

    type: str = Field(..., description="Type of classification (sic, soc)")
    classified: bool = Field(..., description="Whether the input was classified")
    followup: Optional[str] = Field(None, description="Follow-up question if needed")
    code: Optional[str] = Field(None, description="The classification code")
    description: Optional[str] = Field(
        None, description="The classification description"
    )
    candidates: list[GenericCandidate] = Field(
        ..., description="List of potential classifications"
    )
    reasoning: str = Field(..., description="Reasoning behind the classification")


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
    code: Optional[str] = Field(None, description="The matched code")
    code_division: Optional[str] = Field(None, description="The code division")
    potential_codes_count: int = Field(
        ..., description="Number of potential codes found"
    )
    potential_divisions: list[PotentialDivision] = Field(
        ..., description="List of potential divisions"
    )
    potential_codes: list[PotentialCode] = Field(
        ..., description="List of potential codes"
    )


class SuggestionQuery(BaseModel):
    """One search sent to /suggestions."""

    value: str = Field(..., description="The search string sent to /suggestions")
    time_start: datetime = Field(..., description="When that search response started")
    time_end: datetime = Field(..., description="When that search response ended")


class SuggestionListItem(BaseModel):
    """One item from the last suggestions list shown to the person."""

    code: str = Field(..., description="Industry code shown for this list item")
    description: str = Field(..., description="Words shown for this list item")


class SuggestionResponse(BaseModel):
    """What the person did with the last suggestions list.

    Stored as sent. The API does not look up or derive an industry code.
    """

    listed: bool = Field(
        ..., description="Whether the person selected an item from the list"
    )
    code: str = Field(
        ...,
        description="Industry code for the selection, or 99999 when none is available",
    )
    description: str = Field(
        ...,
        description="The item chosen from the list. Empty when listed is false",
    )
    suggestions: list[SuggestionListItem] = Field(
        ...,
        description=(
            "Last /suggestions list only, in the order shown. "
            "Element 0 is the top of the list"
        ),
    )
    not_listed_description: str = Field(
        ...,
        description=(
            "Empty when listed is true. Otherwise the text entered after Not listed"
        ),
    )


class SurveyAssistInteraction(BaseModel):
    """Model for survey assist interaction."""

    type: str = Field(
        ...,
        description="Interaction type (classify or lookup)",
        pattern="^(classify|lookup)$",
    )
    flavour: str = Field(
        ..., description="Classification flavour (sic or soc)", pattern="^(sic|soc)$"
    )
    time_start: datetime = Field(..., description="Start time of the interaction")
    time_end: datetime = Field(..., description="End time of the interaction")
    input: list[InputField] = Field(..., description="Input data for the interaction")
    response: Union[ClassificationResponse, LookupResponse] = Field(
        ..., description="Response from the interaction"
    )


class SuggestionInteraction(BaseModel):
    """A search-as-you-type interaction stored on a survey result."""

    type: str = Field(
        ...,
        description="Interaction type (suggestion)",
        pattern="^suggestion$",
    )
    flavour: str = Field(
        ..., description="Classification flavour (sic or soc)", pattern="^(sic|soc)$"
    )
    time_start: datetime = Field(..., description="When the SAYT question is shown")
    time_end: datetime = Field(..., description="When the SAYT question is answered")
    input: list[InputField] = Field(
        ...,
        description="Survey answers up to the point the result was sent",
    )
    queries_sent: int = Field(
        ..., description="Number of individual searches sent to /suggestions"
    )
    queries: list[SuggestionQuery] = Field(
        ..., description="Each search sent to /suggestions"
    )
    response: SuggestionResponse = Field(
        ..., description="The selection or Not listed outcome, and the last list"
    )


class GenericSurveyAssistInteraction(BaseModel):
    """Model for generic survey assist interaction that can handle SIC or SOC."""

    type: str = Field(
        ...,
        description="Interaction type (classify or lookup)",
        pattern="^(classify|lookup)$",
    )
    flavour: str = Field(
        ...,
        description="Classification flavour (sic, soc, or sic_soc)",
        pattern="^(sic|soc|sic_soc)$",
    )
    time_start: datetime = Field(..., description="Start time of the interaction")
    time_end: datetime = Field(..., description="End time of the interaction")
    input: list[InputField] = Field(..., description="Input data for the interaction")
    response: Union[list[GenericClassificationResult], LookupResponse] = Field(
        ..., description="Response from the interaction"
    )


class Response(BaseModel):
    """Model for a single response."""

    person_id: str = Field(..., description="Identifier for the person")
    time_start: datetime = Field(..., description="Start time of the response")
    time_end: datetime = Field(..., description="End time of the response")
    survey_assist_interactions: list[
        Union[SurveyAssistInteraction, SuggestionInteraction]
    ] = Field(..., description="List of survey assist interactions")


class GenericResponse(BaseModel):
    """Model for a single generic response that can handle SIC or SOC."""

    person_id: str = Field(..., description="Identifier for the person")
    time_start: datetime = Field(..., description="Start time of the response")
    time_end: datetime = Field(..., description="End time of the response")
    survey_assist_interactions: list[GenericSurveyAssistInteraction] = Field(
        ..., description="List of survey assist interactions"
    )


class SurveyAssistResult(BaseModel):
    """Model for the complete survey assist result."""

    survey_id: str = Field(
        ..., description="Identifier for the survey", examples=["test-survey-123"]
    )
    case_id: str = Field(
        ..., description="Identifier for the case", examples=["test-case-456"]
    )
    wave_id: str = Field(
        ..., description="Identifier for the wave", examples=["wave-789"]
    )
    user: str = Field(
        ...,
        description="User identifier in format 'name.surname'",
        examples=["test.userSA187"],
    )
    time_start: datetime = Field(
        ..., description="Start time of the survey", examples=["2024-03-19T10:00:00Z"]
    )
    time_end: datetime = Field(
        ..., description="End time of the survey", examples=["2024-03-19T10:05:00Z"]
    )
    responses: list[Response] = Field(..., description="List of responses")


class GenericSurveyAssistResult(BaseModel):
    """Model for the complete generic survey assist result that can handle SIC or SOC."""

    survey_id: str = Field(
        ..., description="Identifier for the survey", examples=["test-survey-123"]
    )
    case_id: str = Field(
        ..., description="Identifier for the case", examples=["test-case-456"]
    )
    wave_id: str = Field(
        ..., description="Identifier for the wave", examples=["wave-789"]
    )
    user: str = Field(
        ...,
        description="User identifier in format 'name.surname'",
        examples=["test.userSA187"],
    )
    time_start: datetime = Field(
        ..., description="Start time of the survey", examples=["2024-03-19T10:00:00Z"]
    )
    time_end: datetime = Field(
        ..., description="End time of the survey", examples=["2024-03-19T10:05:00Z"]
    )
    responses: list[GenericResponse] = Field(..., description="List of responses")


class ResultResponse(BaseModel):
    """Response model for result endpoints."""

    message: str = Field(..., description="Response message")
    result_id: Optional[str] = Field(
        None, description="Unique identifier for the stored result"
    )


class ResultWithId(SurveyAssistResult):
    """Model for survey result with document ID."""

    document_id: str = Field(..., description="Firestore document ID")


class ListResultsResponse(BaseModel):
    """Response model for list results endpoint."""

    results: list[ResultWithId] = Field(..., description="List of matching results")
    count: int = Field(..., description="Number of results returned")
