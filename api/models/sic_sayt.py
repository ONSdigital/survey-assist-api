"""Models for the SIC search-as-you-type endpoint."""

from pydantic import BaseModel, Field


class SICSaytResponse(BaseModel):
    """Response model for SIC search-as-you-type suggestions."""

    suggestions: list[str] = Field(default_factory=list)


SIC_SAYT_RESPONSE_EXAMPLE = SICSaytResponse(
    suggestions=[
        "Street lighting installation",
        "Installation and maintenance of refrigeration",
        "Insulating activities",
    ]
).model_dump()
