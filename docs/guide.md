# Survey Assist API Guide

## Overview

The Survey Assist API is a FastAPI-based service that provides endpoints for industrial classification and data storage. This guide provides detailed information about the API's features, setup, and usage.

## Architecture

The API is built using:
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **SIC Classification Library**: Core classification functionality
- **Vector Store Service**: Embeddings and semantic search capabilities

## API Endpoints

### Configuration Endpoint
- **Path**: `/v1/survey-assist/config`
- **Method**: GET
- **Description**: Returns the current configuration settings including:
  - LLM model configuration
  - Data store settings
  - Classification prompts
  - Version-specific settings

### Classification Endpoint
- **Path**: `/v1/survey-assist/classify`
- **Method**: POST
- **Description**: Classifies job titles and descriptions into SIC codes using vector store similarity search and LLM models
- **Request Body**:
  - `llm` (required): The LLM model to use ("chat-gpt" or "gemini")
  - `type` (required): Type of classification ("sic", "soc", or "sic_soc")
  - `job_title` (required): Survey response for Job Title
  - `job_description` (required): Survey response for Job Description
  - `org_description` (optional): Survey response for Organisation/Industry Description
- **Response**: Returns classification results including:
  - `classified` (boolean): Whether the input could be definitively classified
  - `followup` (string, optional): Additional question to help classify
  - `sic_code` (string, optional): The SIC code (empty if classified=False)
  - `sic_description` (string, optional): The SIC code description (empty if classified=False)
  - `sic_candidates` (array): List of potential SIC code candidates with:
    - `sic_code` (string): The SIC code
    - `sic_descriptive` (string): The SIC code description
    - `likelihood` (number): Confidence score between 0 and 1
  - `reasoning` (string): Reasoning behind the classification

The classification process works as follows:
1. The input text is used to search the vector store for similar SIC codes
2. The vector store returns a list of candidates with similarity scores
3. The LLM analyzes the candidates and input to determine the final classification
4. If the classification is ambiguous, a follow-up question is provided

### Result Endpoint
- **Path**: `/v1/survey-assist/result`
- **Method**: POST
- **Description**: Stores classification results for later retrieval and analysis
- **Request Body**:
  - `user_id` (required): Unique identifier for the user
  - `survey` (required): Name of the survey
  - `job_title` (required): Survey response for Job Title
  - `job_description` (required): Survey response for Job Description
  - `org_description` (required): Survey response for Organisation/Industry Description
- **Response**: Returns stored result information:
  - `user_id`: The user ID from the request
  - `survey`: The survey name from the request

### SIC Lookup Endpoint
- **Path**: `/v1/survey-assist/sic-lookup`
- **Method**: GET
- **Parameters**:
  - `description` (required): The business description to classify
  - `similarity` (optional): Boolean flag for similarity search
- **Description**: Performs SIC code lookup with two modes:
  - Exact match (similarity=false)
  - Similarity search (similarity=true)

### Embeddings Endpoint
- **Path**: `/v1/survey-assist/embeddings`
- **Method**: GET
- **Description**: Checks the status of the vector store service and its embeddings
- **Response**: Returns the current status of the vector store service
- **Error Handling**: Returns a 503 Service Unavailable status if the vector store service is not accessible

## Integration with External Services

### SIC Classification Library
The API integrates with the SIC Classification Library to provide:
- Standard Industrial Classification (SIC) code lookup
- Similarity-based classification
- Metadata for classifications
- Code division information

### Vector Store Service
The API integrates with the Vector Store Service to provide:
- Status checking for embeddings availability
- Error handling for service unavailability
- Asynchronous communication with the vector store

## Documentation

### Interactive Documentation
The API provides two types of interactive documentation:
1. **Swagger UI** (`/docs`)
   - Interactive API testing
   - Request/response schemas
   - Example values
   - Try-it-out functionality

2. **ReDoc** (`/redoc`)
   - Alternative documentation view
   - Clean, readable format
   - Schema visualisation

You can access these interactive documentation tools by ensuring your API is running and then navigating to the `/docs` or `/redoc` URL in a browser (e.g., http://127.0.0.1:8080/docs).

### API Specification
The OpenAPI specification is available at `/openapi.json`

## Development

### Prerequisites
- Python 3.12
- Poetry for dependency management
- Access to the SIC Classification Library
- Access to the Vector Store Service

### Setup
1. Clone the repositories:
   ```bash
   # Clone survey-assist-api
   git clone https://github.com/ONSdigital/survey-assist-api.git
   cd survey-assist-api
   poetry install

   # Clone vector store service
   git clone https://github.com/ONSdigital/sic-classification-vector-store.git
   cd sic-classification-vector-store
   poetry install
   ```

2. Start both services (in separate terminal windows):
   ```bash
   # Terminal 1 - Start the vector store service
   cd sic-classification-vector-store
   make run-vector-store

   # Terminal 2 - Start the survey assist API
   cd survey-assist-api
   make run-api
   make run-docs
   ```

3. Access the services:
   - Survey Assist API: http://localhost:8080
   - Documentation: http://localhost:8000
   - Vector Store: http://localhost:8088 (default port, configurable via SIC_VECTOR_STORE environment variable)

Note: Both services must be running simultaneously for the embeddings endpoint to work. The vector store service must be started before making requests to the `/embeddings` endpoint.

### Testing
The project includes comprehensive test coverage:
- API endpoint tests
- Client service tests
- Error handling tests
- Integration tests with external services

Tests can be run using:
```bash
make api-tests  # For API endpoint tests
make unit-tests # For unit tests
make all-tests  # For all tests
```

### Code Quality
Code quality is maintained through:
- Static type checking with mypy
- Linting with pylint and ruff
- Code formatting with black
- Security checking with bandit
- Documentation with mkdocs

## Error Handling

The API implements robust error handling:
- Validation errors for invalid requests
- Service unavailability errors for external services
- Detailed error messages for debugging
- Proper HTTP status codes for different error scenarios

## Configuration

The API provides a configuration system that currently allows viewing the active configuration.

- The `/config` endpoint provides a read-only view of the current API configuration.
- Currently, the LLM configuration is static and cannot be modified via the API.

Configuration is managed through the `/config` endpoint and reflects the settings currently in use.

## Security

The API is designed to be deployed with:
- JWT authentication
- API Gateway integration
- Secure data storage
- Environment-specific configurations

## Contributing

Please refer to the project's contribution guidelines for information on:
- Code style
- Testing requirements
- Documentation standards
- Pull request process
