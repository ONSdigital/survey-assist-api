"""This module contains the models for the configuration response.

The models in this module are used to represent the configuration response
returned by the API.
"""

from pydantic import BaseModel


class PromptModel(BaseModel):
    """Model representing a prompt.

    Attributes:
        name (str): The name of the prompt.
        text (str): The text of the prompt.
    """

    name: str
    text: str


class ClassificationModel(BaseModel):
    """Model representing a classification.

    Attributes:
        type (str): The type of the classification.
        prompts (list[PromptModel]): A list of prompts associated with the classification.
    """

    type: str
    prompts: list[PromptModel]


class ConfigResponse(BaseModel):
    """Model representing the configuration response.

    Attributes:
        llm_model (str): The name of the language model.
        data_store (str): The data store used.
        bucket_name (str): The name of the bucket.
        v1v2 (dict[str, list[ClassificationModel]]):
          A dictionary mapping v1 and 2 to their classifications.
        v3 (dict[str, list[ClassificationModel]]):
          A dictionary mapping v3 to its classifications.
    """

    llm_model: str
    data_store: str
    bucket_name: str
    v1v2: dict[str, list[ClassificationModel]]
    v3: dict[str, list[ClassificationModel]]
