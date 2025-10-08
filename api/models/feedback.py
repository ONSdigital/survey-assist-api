"""Module that provides the models for the feedback endpoint.

This module contains the request and response models for the feedback endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from typing import Optional

from pydantic import BaseModel, Field


class FeedbackResponse(BaseModel):
    """Model for a single feedback response."""

    question: str = Field(..., description="Question text")
    options: Optional[list[str]] = Field(
        None, description="Optional list of radio selections for multi choice"
    )
    answer: str = Field(..., description="Answer text")


class FeedbackPerson(BaseModel):
    """Model for feedback per person."""

    person_id: str = Field(..., description="Unique identifier for the person")
    response: list[FeedbackResponse] = Field(
        ..., description="List of feedback responses"
    )


class FeedbackRequest(BaseModel):
    """Model for the feedback request."""

    case_id: str = Field(..., description="Case identifier")
    feedback: list[FeedbackPerson] = Field(
        ..., description="List of feedback per person"
    )


class FeedbackResponseModel(BaseModel):
    """Response model for feedback endpoints."""

    message: str = Field(..., description="Response message")
