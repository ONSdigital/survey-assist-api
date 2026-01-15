# Survey Assist API

The Survey Assist API is a FastAPI service that provides SIC (Standard Industrial Classification) support (lookup and LLM-assisted classification), plus optional storage of results and feedback in Firestore.

## Key Features

- **SIC classification**: `POST /v1/survey-assist/classify` performs a two-step SIC classification using a vector-store shortlist and a Gemini LLM.
- **SIC lookup**: `GET /v1/survey-assist/sic-lookup` looks up SIC codes by description (with optional similarity search).
- **Vector store status**: `GET /v1/survey-assist/embeddings` checks whether SIC embeddings are ready to query.
- **Configuration introspection**: `GET /v1/survey-assist/config` returns the LLM model name, embedding model (from the vector store), and prompt templates.
- **Firestore-backed persistence (optional)**:
  - `POST /v1/survey-assist/result`, `GET /v1/survey-assist/result`, `GET /v1/survey-assist/results`
  - `POST /v1/survey-assist/feedback`

## API Documentation

The API documentation is available in two formats:
- **Swagger UI**: Interactive documentation at `/swagger2/docs`
- **ReDoc**: Alternative documentation view at `/swagger2/redoc`

All versioned endpoints are mounted under `/v1/survey-assist`. The root endpoint (`GET /`) returns a simple “API is running” message.

## Getting Started

For detailed information on installation, setup, and usage, please refer to the [Guide](guide.md).

## Configuration

- **`SIC_VECTOR_STORE`**: Base URL for the SIC vector store (defaults to `http://localhost:8088`).
- **`SIC_LOOKUP_DATA_PATH`**: Optional path to a SIC lookup CSV. If unset, packaged example data is used.
- **`SIC_REPHRASE_DATA_PATH`**: Optional path to a rephrased SIC CSV. If unset, packaged example data is used.
- **`FIRESTORE_DB_ID`**: Enables Firestore-backed endpoints when set; if unset, result/feedback endpoints will fail because the Firestore client is not initialised.
- **`GCP_PROJECT_ID`**: Optional; used when initialising Firestore.

## Notes

- **SOC classification is not implemented yet**: requests with `type="soc"`/`"sic_soc"` return a placeholder SOC result at present.

## Further reading

- [Guide](guide.md)
- [Generic classification](generic_classification.md)
- [GCP deployment](gcp_deployment.md)
