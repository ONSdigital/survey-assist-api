"""Module that provides the models for the feedback endpoint.

This module contains the request and response models for the feedback endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from typing import Optional

from pydantic import BaseModel, Field


class FeedbackQuestionMod(BaseModel):
    """Feedback question structure.

    response - the answer to the question.
    response_name - the id associated with the question.
    response_options - list of options provided for radio questions.
    """

    response: str = Field(..., description="User response")
    response_name: str = Field(..., description="UI Response Name")
    response_options: list[str] | None = Field(
        ..., description="Radio selection options"
    )  # only present for radio questions


class FeedbackResult(BaseModel):
    """Feedback result.

    case_id - the unique id associated with (typically) the household.
    person_id - the unique id associated with a respondent in the household.
    survey_id - the unique id for the survey
    wave_id - the unique id for the wave
    questions - list of questions used to gather respondent feedback.
    """

    case_id: str = Field(..., description="Unique id for group")
    person_id: str = Field(..., description="Unique id for person")
    survey_id: str = Field(..., description="Unique id for survey")
    wave_id: str = Field(..., description="Unique id for wave")
    questions: list[FeedbackQuestionMod] = Field(
        ..., description="List of follow-up questions"
    )


class FeedbackResultResponse(BaseModel):
    """Response model for feedback endpoints."""

    message: str = Field(..., description="Feedback response message")
    feedback_id: Optional[str] = Field(
        None, description="Unique identifier for the stored feedback"
    )


class FeedbackWithId(FeedbackResult):
    """Model for feedback result with document ID."""

    document_id: str = Field(..., description="Firestore document ID")


class ListFeedbacksResponse(BaseModel):
    """Response model for list feedbacks endpoint."""

    results: list[FeedbackWithId] = Field(
        ..., description="List of matching feedback results"
    )
    count: int = Field(..., description="Number of results returned")
