"""Module that provides the configuration endpoint for the Survey Assist API.

This module contains the configuration endpoint for the Survey Assist API.
It defines the configuration endpoint and returns the current configuration settings.
"""

from fastapi import APIRouter

from api.models.config import ClassificationModel, ConfigResponse, PromptModel

router: APIRouter = APIRouter(tags=["Configuration"])

# Mock configuration
config_data: ConfigResponse = ConfigResponse(
    llm_model="gpt-4",
    data_store="some_data_store",
    bucket_name="my_bucket",
    v1v2={
        "classification": [
            ClassificationModel(
                type="sic",
                prompts=[
                    PromptModel(name="SA_SIC_PROMPT_RAG", text="my SIC RAG prompt"),
                ],
            )
        ]
    },
    v3={
        "classification": [
            ClassificationModel(
                type="sic",
                prompts=[
                    PromptModel(name="SIC_PROMPT_RERANKER", text="my reranker prompt"),
                    PromptModel(
                        name="SIC_PROMPT_UNAMBIGUOUS", text="my unambiguous prompt"
                    ),
                ],
            )
        ]
    },
)


@router.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Get the current configuration.

    Returns:
        ConfigResponse: A dictionary containing the current configuration settings.

    Example:
        ```json
        {
            "llm_model": "gpt-4",
            "data_store": "some_data_store",
            "bucket_name": "my_bucket",
            "v1v2": {
                "classification": [
                    {
                        "type": "sic",
                        "prompts": [
                            {
                                "name": "SA_SIC_PROMPT_RAG",
                                "text": "my SIC RAG prompt"
                            }
                        ]
                    }
                ]
            },
            "v3": {
                "classification": [
                    {
                        "type": "sic",
                        "prompts": [
                            {
                                "name": "SIC_PROMPT_RERANKER",
                                "text": "my reranker prompt"
                            },
                            {
                                "name": "SIC_PROMPT_UNAMBIGUOUS",
                                "text": "my unambiguous prompt"
                            }
                        ]
                    }
                ]
            }
        }
        ```
    """
    return config_data
