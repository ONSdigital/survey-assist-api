"""Module that provides the models for the result endpoint.

This module contains the request and response models for the result endpoint.
It defines the structure of the data that can be sent to and received from the endpoint.
"""

from pydantic import BaseModel, Field


class ResultRequest(BaseModel):
    """Model representing a result request.

    Attributes:
        user_id (str): The unique identifier for the user.
        survey (str): The name of the survey.
        job_title (str): Survey response for Job Title.
        job_description (str): Survey response for Job Description.
        org_description (str): Survey response for Organisation/Industry Description.
    """

    user_id: str = Field(..., description="The unique identifier for the user")
    survey: str = Field(..., description="The name of the survey")
    job_title: str = Field(..., description="Survey response for Job Title")
    job_description: str = Field(..., description="Survey response for Job Description")
    org_description: str = Field(
        ..., description="Survey response for Organisation/Industry Description"
    )


class ResultResponse(BaseModel):
    """Model representing a result response.

    Attributes:
        user_id (str): The unique identifier for the user.
        survey (str): The name of the survey.
    """

    user_id: str = Field(..., description="The unique identifier for the user")
    survey: str = Field(..., description="The name of the survey")
