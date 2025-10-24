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
        firestore_database_id (str): The Firestore database ID.
        v1v2 (dict[str, list[ClassificationModel]]):
          A dictionary mapping v1 and 2 to their classifications.
        v3 (dict[str, list[ClassificationModel]]):
          A dictionary mapping v3 to its classifications.
        embedding_model (str | None): The name of the embedding model (optional).
        actual_prompt (str | None): The actual prompt used by the LLM (optional).
    """

    llm_model: str
    data_store: str
    firestore_database_id: str
    v1v2: dict[str, list[ClassificationModel]]
    v3: dict[str, list[ClassificationModel]]
    embedding_model: str | None = None
    actual_prompt: str | None = None
