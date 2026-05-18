"""This module contains the models for the status response.

The models in this module are used to represent the response
returned by the embeddings endpoint in the API.
"""

from industrial_classification_utils.models.config_model import EmbeddingStatus


EMBEDDINGS_STATUS_EXAMPLE = EmbeddingStatus(
    status="ready",
    embedding_model_name="all-MiniLM-L6-v2",
    db_dir="src/sic_classification_vector_store/data/vector_store",
    index_source_file="gs://bucket/sic_vector_store_data/sic_kb_for_classifai.csv",
    k_matches=20,
    index_size=16618,
).model_dump()
