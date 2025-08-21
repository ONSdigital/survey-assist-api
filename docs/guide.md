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
  - LLM model configuration (`llm_model`)
  - Vector store embedding model (`embedding_model`)
  - LLM model configuration (`llm_model`)
  - Vector store embedding model (`embedding_model`)
  - Data store settings
  - Classification prompts (per version)
  - Version-specific settings
  - Actual prompt used by the LLM (`actual_prompt`)
- **Response Example**:
  ```json
  {
    "llm_model": "gemini-1.5-flash",
    "embedding_model": "all-MiniLM-L6-v2",
    "data_store": "some_data_store",
    "bucket_name": "my_bucket",
    "actual_prompt": "You are a classification assistant. Given the following information: Job Title: Test job title...",
    "v1v2": {
      "classification": [
        {
          "type": "sic",
          "prompts": [
            { "name": "SA_SIC_PROMPT_RAG", "text": "my SIC RAG prompt" }
          ]
        }
      ]
    },
    "v3": {
      "classification": [
        {
          "type": "sic",
          "prompts": [
            { "name": "SIC_PROMPT_RERANKER", "text": "my reranker prompt" },
            { "name": "SIC_PROMPT_UNAMBIGUOUS", "text": "my unambiguous prompt" }
          ]
        }
      ]
    }
  }
  ```

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
3. The LLM analyses the candidates and input to determine the final classification
4. If the classification is ambiguous, a follow-up question is provided

### Result Endpoint
- **Base URL**: `http://localhost:8080`
- **Path**: `/v1/survey-assist/result`
- **Method**: POST
- **Description**: Stores classification results for later retrieval and analysis
- **Request Body**:
  ```json
  {
    "survey_id": "test-survey-123",
    "case_id": "test-case-456",
    "time_start": "2024-03-19T10:00:00Z",
    "time_end": "2024-03-19T10:05:00Z",
    "responses": [
      {
        "person_id": "person-1",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:01:00Z",
        "survey_assist_interactions": [
          {
            "type": "classify",
            "flavour": "sic",
            "time_start": "2024-03-19T10:00:00Z",
            "time_end": "2024-03-19T10:01:00Z",
            "input": [
              {
                "field": "job_title",
                "value": "Electrician"
              }
            ],
            "response": {
              "classified": true,
              "code": "432100",
              "description": "Electrical installation",
              "reasoning": "Based on job title and description",
              "candidates": [
                {
                  "code": "432100",
                  "description": "Electrical installation",
                  "likelihood": 0.95
                }
              ],
              "follow_up": {
                "questions": []
              }
            }
          }
        ]
      }
    ]
  }
  ```
- **Response**: Returns stored result information:
  ```json
  {
    "message": "Result stored successfully",
    "result_id": "test-survey-123/test.userSA187/2024-03-19/10_30_15.json"
  }
  ```

### Get Result Endpoint
- **Base URL**: `http://localhost:8080`
- **Path**: `/v1/survey-assist/result`
- **Method**: GET
- **Description**: Retrieves stored classification results
- **Query Parameters**:
  - `result_id` (required): The ID of the result to retrieve (e.g., "test-survey-123/test.userSA187/2024-03-19/10_30_15.json")
- **Response**: Returns the stored result in the same format as the POST request body.

### Example Usage
```bash
# Store a result
curl -X POST "http://localhost:8080/v1/survey-assist/result" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": "test-survey-123",
    "case_id": "test-case-456",
    "time_start": "2024-03-19T10:00:00Z",
    "time_end": "2024-03-19T10:05:00Z",
    "responses": [
      {
        "person_id": "person-1",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:01:00Z",
        "survey_assist_interactions": [
          {
            "type": "classify",
            "flavour": "sic",
            "time_start": "2024-03-19T10:00:00Z",
            "time_end": "2024-03-19T10:01:00Z",
            "input": [
              {
                "field": "job_title",
                "value": "Electrician"
              }
            ],
            "response": {
              "classified": true,
              "code": "432100",
              "description": "Electrical installation",
              "reasoning": "Based on job title and description",
              "candidates": [
                {
                  "code": "432100",
                  "description": "Electrical installation",
                  "likelihood": 0.95
                }
              ],
              "follow_up": {
                "questions": []
              }
            }
          }
        ]
      }
    ]
  }'

# Retrieve a result
curl -X GET "http://localhost:8080/v1/survey-assist/result?result_id=test-survey-123/test.userSA187/2024-03-19/10_30_15.json"
```

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
1. **Swagger UI** (`/swagger2/docs`)
   - Interactive API testing
   - Request/response schemas
   - Example values
   - Try-it-out functionality

2. **ReDoc** (`/swagger2/redoc`)
   - Alternative documentation view
   - Clean, readable format
   - Schema visualisation

You can access these interactive documentation tools by ensuring your API is running and then navigating to the `/swagger2/docs` or `/swagger2/redoc` URL in a browser (e.g., http://127.0.0.1:8080/swagger2/docs).

### API Specification
The Swagger2 specification is available at `/swagger2.json`

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

## Local Development with Docker

### Prerequisites for Docker Setup
- Docker installed and running
- Colima (for macOS) or Docker Desktop
- Google Cloud CLI (`gcloud`) authenticated
- Access to the `survey-assist-sandbox` GCP project

### Docker Setup

#### 1. Build the Docker Image
Navigate to the survey-assist-api directory and build the image:
```bash
cd survey-assist-api
docker build -t sa_api .
```

**Note**: The build process requires significant memory (recommended: 8GB+). If using Colima, ensure sufficient resources:
```bash
colima start --memory 8 --cpu 4
```

#### 2. Set Up Google Cloud Authentication
Ensure you're authenticated and have access to the required project:
```bash
# Check current authentication
gcloud auth list

# Set the active project
gcloud config set project survey-assist-sandbox

# Create service account key (if needed)
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=sa-tlfs-vertexai@survey-assist-sandbox.iam.gserviceaccount.com
```

#### 3. Start the Vector Store Service
In a separate terminal, start the vector store service locally:
```bash
cd sic-classification-vector-store
make run-vector-store
```

#### 4. Get Host Machine IP Address
Get the IP address of your host machine (not the Colima VM):
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
Look for your local network IP address (usually starts with `192.168.x.x` or `10.x.x.x`).

**Important:** We use the **host machine's IP address**, not the Colima VM's IP address, because the container needs to connect to services running on the host machine itself.

#### 5. Run the API Container
Run the survey assist API container with the proper configuration:
```bash
docker run \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json \
  -e SIC_VECTOR_STORE=http://<host-ip-address>:8088 \
  sa_api
```

**Environment Variables Explained:**
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the service account key file inside the container
- `SIC_VECTOR_STORE`: URL of the locally running vector store service

**Volume Mount:**
- Maps the local `service-account-key.json` to `/app/service-account-key.json` inside the container

**Note:** Port forwarding (`-p 8080:8080`) is not strictly necessary on macOS as Docker Desktop automatically provides host access to container ports. However, if you prefer explicit port forwarding, you can add `-p 8080:8080` to the command.

### Alternative: Run in Background
To run the container in the background:
```bash
docker run -d \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json \
  -e SIC_VECTOR_STORE=http://<host-ip-address>:8088 \
  --name survey-assist-api \
  sa_api
```

### Testing the Setup

#### 1. Verify Vector Store
Ensure the vector store is accessible:
```bash
curl http://localhost:8088/health
```

#### 2. Test API Endpoints
Test the survey assist API:
```bash
# Health check
curl http://localhost:8080/health

# Configuration
curl http://localhost:8080/v1/survey-assist/config

# Test classification (example)
curl -X POST http://localhost:8080/v1/survey-assist/classify \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Farmer",
    "job_description": "Grows crops and raises livestock",
    "org_description": "Agricultural farm"
  }'
```

### Troubleshooting

#### Common Issues

**Port Already in Use**
```bash
# Check what's using the port
lsof -i :8088

# Kill the process if needed
kill <PID>
```

**Docker Build Memory Issues**
```bash
# Increase Colima memory
colima stop
colima start --memory 8 --cpu 4
```

**Service Account Permission Issues**
```bash
# Verify the service account has the right roles
gcloud projects get-iam-policy survey-assist-sandbox \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:sa-tlfs-vertexai@survey-assist-sandbox.iam.gserviceaccount.com"
```

**Network Connectivity Issues**
```bash
# Test connectivity from container to host
docker exec <container_id> curl http://<host-ip-address>:8088/health

# Verify Colima VM is running
colima status

# If using port forwarding, verify ports are correctly mapped
docker port <container_id>
```

### Development Workflow

1. **Make code changes** in the survey-assist-api directory
2. **Rebuild the image** when dependencies change:
   ```bash
   docker build -t sa_api .
   ```
3. **Restart the container** with the new image
4. **Test changes** using the API endpoints
5. **Iterate** on the development cycle

### Simplified Setup Notes

The local Docker setup has been simplified and tested:
- **No `--network=host` required**: This flag doesn't work properly on macOS Docker Desktop
- **No port forwarding required**: Docker Desktop on macOS automatically provides host access to container ports
- **Use host machine IP (NOT VM IP)**: The container connects to `http://<host-ip-address>:8088` for the vector store
- **Cleaner commands**: The Docker run commands are now simpler and more reliable

**Key Point:** We use the **host machine's actual IP address** (like `192.168.1.157`), not the Colima VM's IP address, because the vector store is running on the host machine itself.

This setup has been verified to work successfully for local development and testing.

### Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | `/app/service-account-key.json` |
| `SIC_VECTOR_STORE` | Vector store service URL | `http://<host-ip-address>:8088` |
| `SIC_LOOKUP_DATA_PATH` | Path to SIC lookup data file | `data/sic_knowledge_base_utf8.csv` |
| `SIC_REPHRASE_DATA_PATH` | Path to SIC rephrase data file | `data/sic_rephrased_descriptions_2025_02_03.csv` |
| `PORT` | API port (default: 8080) | `8080` |

### Security Notes

- **Never commit** `service-account-key.json` to version control
- **Rotate keys** regularly for production use
- **Use least privilege** principle when assigning IAM roles
- **Monitor usage** through GCP Cloud Logging

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

The API provides a configuration system that manages various settings including data file paths and service configurations.

### Configuration Options

- **Data File Paths**: Configurable paths for SIC lookup and rephrase data files
- **Service Settings**: GCP bucket names, vector store URLs, and other service configurations
- **Environment Variables**: All settings can be overridden via environment variables

### Data File Configuration

The API now loads data files from configurable paths instead of hardcoded locations:

- **SIC Lookup Data**: `SIC_LOOKUP_DATA_PATH` (default: `data/sic_knowledge_base_utf8.csv`)
- **SIC Rephrase Data**: `SIC_REPHRASE_DATA_PATH` (default: `data/sic_rephrased_descriptions_2025_02_03.csv`)

### Viewing Configuration

- The `/config` endpoint provides a read-only view of the current API configuration
- Currently, the LLM configuration is static and cannot be modified via the API

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
