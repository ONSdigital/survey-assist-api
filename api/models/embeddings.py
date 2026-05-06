"""This module contains the models for the status response.

The models in this module are used to represent the response
returned by the embeddings endpoint in the API.
"""

from pydantic import BaseModel


class FileSource(BaseModel):
    """Model representing a file source for the vector store.

    Attributes:
        package (str): The name of the package containing the file.
        file (str): The name of the file.
    """

    package: str
    file: str


class StatusResponse(BaseModel):
    """Model representing the vector store status response.

    Attributes:
        embedding_model_name (str): The name of the embeddings model.
        db_dir (str): The vector store directory.
        sic_index_source (FileSource): The SIC index source file.
        sic_structure_source (FileSource): The SIC structure source file.
        sic_condensed_source (FileSource): The condensed SIC reference file.
        matches (int): The number of nearest matches initialised in the vector store.
        index_size (int): The number of embedded entries in the vector store.
        status (str): The status of the vector store.
    """

    status: str
    embedding_model_name: str
    db_dir: str
    sic_index_source: FileSource
    sic_structure_source: FileSource
    sic_condensed_source: FileSource
    matches: int
    index_size: int


EMBEDDINGS_STATUS_EXAMPLE = StatusResponse(
    status="ready",
    embedding_model_name="text-embedding-004",
    db_dir="/app/data/vector_store",
    sic_index_source=FileSource(
        package="industrial_classification_utils",
        file="data/sic_2007_index.csv",
    ),
    sic_structure_source=FileSource(
        package="industrial_classification_utils",
        file="data/sic_2007_structure.xlsx",
    ),
    sic_condensed_source=FileSource(
        package="industrial_classification_utils",
        file="data/sic_2007_condensed.csv",
    ),
    matches=20,
    index_size=1234,
).model_dump()
