# Survey Assist API

The Survey Assist API is a FastAPI service that provides access to classification services to determine which industry or occupation a respondent works in. Standard Industrial Code (SIC) classification is implemented using a direct lookup against an internal knowledge-base and if the classification cannot be made directly an LLM will attempt to unambiguously classify or provide a follow up question to gain further information. Standard Occupation Classification (SOC) is a future enhancement and the current endpoint will only return a template SOC response. The API provides endpoints to allow the client to store classification results and feedback in a Firestore database.

## Key Features

- **SIC classification**: `POST /v1/survey-assist/classify` performs a two-step SIC classification using a vector-store shortlist and a Gemini LLM.
- **SIC lookup**: `GET /v1/survey-assist/sic-lookup` looks up SIC codes by description (with optional similarity search).
- **Vector store status**: `GET /v1/survey-assist/embeddings` checks whether SIC embeddings are ready to query.
- **Configuration introspection**: `GET /v1/survey-assist/config` returns the LLM model name, embedding model (from the vector store), and prompt templates.
- **Firestore-backed persistence (optional)**:
  - `POST /v1/survey-assist/result`, `GET /v1/survey-assist/result`, `GET /v1/survey-assist/results`
  - `POST /v1/survey-assist/feedback`, `GET /v1/survey-assist/feedback`, `GET /v1/survey-assist/feedbacks`

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

- **SOC classification availability**: SOC classification uses the SOC vector store and a SOC LLM when these services are configured. If the SOC LLM is not available, requests with `type="soc"`/`"sic_soc"` will return a 503 `"SOC classification is not available"` error. SOC rephrasing is available for SOC codes that appear in the SOC rephrase dataset provided by `soc-classification-library`.

## Further reading

- [Guide](guide.md)
- [Generic classification](generic_classification.md)
- [GCP deployment](gcp_deployment.md)
