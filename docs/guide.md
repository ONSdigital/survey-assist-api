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
    "llm_model": "gemini-2.5-flash",
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
  - `rephrase` (optional): Boolean flag for user-friendly language conversion
  - `data_path` (optional): Path to specific dataset within container (e.g., `data/sic_knowledge_base_utf8.csv`)
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

### Data Source Selection

The API supports two data sources for classification and lookup:

**Package Data (Default)**: Uses example datasets from the sic-classification-library package
- Provides basic classification functionality
- Suitable for testing and development
- No additional parameters required
- **Note**: Environment variables for data paths are no longer used

**Full Datasets**: Uses complete datasets copied into the container during build
- Provides comprehensive classification with full metadata
- Includes detailed includes/excludes lists and division information
- The API uses packaged example data by default

**Example Usage with Full Datasets**:
```bash
# SIC Lookup with full dataset
curl --header "Authorization: Bearer ${JWT_TOKEN}" \
  "https://your-api-gateway-url/v1/survey-assist/sic-lookup?description=electrical%20installation"

# Classification with full dataset and rephrase
curl --header "Authorization: Bearer ${JWT_TOKEN}" \
  --header "Content-Type: application/json" \
  --data '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "electrical engineer",
    "job_description": "designing and installing electrical systems",
    "org_description": "electrical contracting company",
    "rephrase": true,
    "data_path": "data/sic_knowledge_base_utf8.csv"
  }' \
  "https://your-api-gateway-url/v1/survey-assist/classify"
```

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
  - `data_path` (optional): Path to specific dataset within container (e.g., `data/sic_knowledge_base_utf8.csv`)
- **Description**: Performs SIC code lookup with two modes:
  - Exact match (similarity=false)
  - Similarity search (similarity=true)
- **Data Sources**: 
  - **Default**: Uses package example data from sic-classification-library
  - **Custom**: The API uses packaged example data by default

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
- Colima for macOS
- Google Cloud CLI (`gcloud`) authenticated
- Access to your GCP project

### Docker Setup

#### 1. Prepare Data Files
Before building the Docker image, you need to create a `data/` folder with the required CSV files:

```bash
# Create the data directory
mkdir -p data

# Add your SIC classification data files to the data/ folder:
# - sic_knowledge_base_utf8.csv (SIC lookup data)
# - sic_rephrased_descriptions_2025_02_03.csv (SIC rephrase data)
```

**Important**: The `data/` folder is not committed to version control (it's in `.gitignore`), so you must create it locally with your data files before building the Docker image.

**Required Data Folder Structure**:
```
survey-assist-api/
├── data/
│   ├── sic_knowledge_base_utf8.csv
│   └── sic_rephrased_descriptions_2025_02_03.csv
├── Dockerfile
├── api/
├── utils/
└── ...
```

#### 2. Build the Docker Image
Navigate to the survey-assist-api directory and build the image:
```bash
cd survey-assist-api
docker build -t sa_api .
```

**Note**: The build process requires significant memory (recommended: 8GB+). If using Colima, ensure sufficient resources:
```bash
colima start --memory 8 --cpu 4
```

**Data Files**: The Docker image will include the SIC classification data files from your local `data/` folder:
- `data/sic_knowledge_base_utf8.csv` - SIC lookup data
- `data/sic_rephrased_descriptions_2025_02_03.csv` - SIC rephrase data

#### 3. Set Up Google Cloud Authentication
The containerized API requires Google Cloud credentials for LLM functionality. You'll need to:

```bash
# Check current authentication
gcloud auth list

# Set the active project (replace with your project ID)
gcloud config set project YOUR_PROJECT_ID

# Create service account key (replace with your service account)
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com
```

**Note**: The API requires GCP credentials to start up due to LLM initialization at startup.

#### 4. Start the Vector Store Service
In a separate terminal, start the vector store service locally:
```bash
cd sic-classification-vector-store
make run-vector-store
```

#### 5. Get Host Machine IP Address
Get the IP address of your host machine (not the Colima VM):
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
Look for your local network IP address (usually starts with `192.168.x.x` or `10.x.x.x`).

**Important:** We use the **host machine's IP address**, not the Colima VM's IP address, because the container needs to connect to services running on the host machine itself.

#### 6. Run the API Container
Run the survey assist API container with the proper configuration:
```bash
docker run \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json \
  -e SIC_VECTOR_STORE=http://<host-ip-address>:8088 \
  -e SIC_REPHRASE_DATA_PATH=data/sic_rephrased_descriptions_2025_02_03.csv \
  -e SIC_LOOKUP_DATA_PATH=data/sic_knowledge_base_utf8.csv \
  sa_api
```

**Environment Variables Explained:**
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the service account key file inside the container
- `SIC_VECTOR_STORE`: URL of the locally running vector store service
- `SIC_REPHRASE_DATA_PATH`: Path to the SIC rephrase data file within the container
- `SIC_LOOKUP_DATA_PATH`: Path to the SIC lookup data file within the container

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
  -e SIC_REPHRASE_DATA_PATH=data/sic_rephrased_descriptions_2025_02_03.csv \
  -e SIC_LOOKUP_DATA_PATH=data/sic_knowledge_base_utf8.csv \
  --name survey-assist-api \
  sa_api
```

### Testing the Setup

#### 1. Verify Data Files Are Loaded
Check the Docker container logs to confirm the data files are loaded successfully:

**Note**: The API currently uses the root endpoint `/` for status checks. Use `curl http://localhost:8080/` to verify the container is running.
```bash
# Get the container ID
docker ps

# Check the logs for data loading messages
docker logs <container_id>
```

**Expected Log Messages**: Look for these indicators that data is loaded:
- SIC lookup data loading messages
- SIC rephrase data loading messages
- No file not found errors for the CSV files

**Example Successful Log Messages**:
```
INFO:api.services.sic_lookup_client:Loaded XXXX SIC lookup codes from data/sic_knowledge_base_utf8.csv
INFO:api.services.sic_rephrase_client:Loaded XXXX rephrased SIC descriptions from data/sic_rephrased_descriptions_2025_02_03.csv
```

**Data Source Confirmation**: 
- **Package Data**: Look for paths containing `industrial_classification_utils/data/example/`
- **Local Data**: Look for paths containing `data/sic_knowledge_base_utf8.csv`

**Note**: Both clients now use the same consistent format: "Loaded XXXX [type] from [filepath]"

**Important**: The SIC lookup uses exact matching. Terms like "farmer" won't match "Arable farmers" - you need to use the exact description from the dataset.

**Warning Signs**: If you see errors like "No such file or directory" or "File not found" for the CSV files, the data hasn't loaded properly.

#### 2. Verify Vector Store
Ensure the vector store is accessible:
```bash
curl http://localhost:8088/health
```

#### 3. Test API Endpoints
Test the survey assist API:
```bash
# Root endpoint (API status)
curl http://localhost:8080/

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

**Note**: The API uses exact matching for SIC lookups. Partial matches (e.g., "farmer" vs "Arable farmers") will not return results.

### Troubleshooting

#### Common Issues

**Data Files Not Loading**
If you see errors about missing data files in the logs:
```bash
# Check if data files exist in the container
docker exec <container_id> ls -la /app/data/

# Verify the data folder structure
docker exec <container_id> find /app -name "*.csv"
```

**Data Loading Behavior**:
- **Package Data (default)**: When no environment variables are set, the API uses example data from the `industrial_classification_utils` package
- **Local Data**: When `SIC_LOOKUP_DATA_PATH` and `SIC_REPHRASE_DATA_PATH` are set, the API uses the full datasets copied into the container during build
- **Exact Matching**: SIC lookups require exact matches (e.g., "Arable farmers" not "farmer")

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
# Verify the service account has the right roles (replace with your project and service account)
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com"
```

**Health Endpoint Note**: The API currently uses the root endpoint `/` for status checks. A dedicated `/health` endpoint is planned for future releases.

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



### Environment Variables Reference

| Variable | Description | Example | Default Behaviour |
|----------|-------------|---------|------------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | `/app/service-account-key.json` | Required for container startup |
| `SIC_VECTOR_STORE` | Vector store service URL | `http://<host-ip-address>:8088` | `http://localhost:8088` |
| `SIC_LOOKUP_DATA_PATH` | Path to SIC lookup data file | `data/sic_knowledge_base_utf8.csv` | Uses package example data |
| `SIC_REPHRASE_DATA_PATH` | Path to SIC rephrase data file | `data/sic_rephrased_descriptions_2025_02_03.csv` | Uses package example data |
| `PORT` | API port | `8080` | `8080` |

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

The API now loads data files from configurable paths. In the Docker container, these files are built into the image:

- **SIC Lookup Data**: `SIC_LOOKUP_PATH` (default: `data/sic_knowledge_base_utf8.csv`)
- **SIC Rephrase Data**: `SIC_REPHRASE_PATH` (default: `data/sic_rephrased_descriptions_2025_02_03.csv`)

**Note**: The data files are now included in the Docker image during the build process, so no external data mounting is required.

### Data Loading Configuration

The Survey Assist API supports flexible data loading with two data sources:

#### **1. Package Data (Default)**
When no environment variables are set, the API automatically uses example datasets from the `sic-classification-library` package:
- **SIC Lookup**: `example_sic_lookup_data.csv` (contains 138 example SIC codes)
- **SIC Rephrase**: `example_rephrased_sic_data.csv` (contains 28 agricultural SIC codes with rephrased descriptions)

#### **2. Local Data (Override)**
When environment variables are set, the API uses custom datasets from specified paths:
- **SIC Lookup**: `SIC_LOOKUP_DATA_PATH` environment variable
- **SIC Rephrase**: `SIC_REPHRASE_DATA_PATH` environment variable

#### **3. Mixed Configuration**
You can mix data sources:
- Local SIC lookup data + Package rephrase data
- Package lookup data + Local rephrase data

### Environment Variables for Data Loading

**Note**: Environment variables for data paths are no longer used. The API always uses packaged example data by default.


### Testing Data Loading Configuration

#### **Test 1: Package Data (No Environment Variables)**
```bash
# Clear any existing environment variables
unset SIC_LOOKUP_DATA_PATH
unset SIC_REPHRASE_DATA_PATH

# Test SIC lookup with package data
curl -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=dairy%20farming"

# Expected response: SIC code 01410 with description "Raising of dairy cattle"

# Test SIC lookup with local data
curl -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=dairy%20farming"
```

#### **Test 2: Local Data (Environment Variables Set)**
```bash
# Note: Environment variables are no longer used for data loading
# The API always uses packaged example data by default

# Test SIC lookup with local data
curl -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=electrician"

# Expected response: SIC code 43210 with description "Electrical installation"
```

#### **Test 3: Mixed Configuration**
```bash
# Note: Environment variables are no longer used for data loading
# The API always uses packaged example data by default

# Test classification with local data
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Dairy Farmer",
    "job_description": "Raising dairy cattle and producing milk"
  }'
```

### Logging and Monitoring

The API provides clear logging about which data sources are being used:

#### **When Using Package Data:**
```
INFO - Loaded [X] SIC lookup codes from [package_path]/example_sic_lookup_data.csv
INFO - Loaded [Y] rephrased SIC descriptions from [package_path]/example_rephrased_sic_data.csv
```

#### **When Using Package Data (Default):**
```
INFO - Loaded [X] SIC lookup codes from [package_path]/example_sic_lookup_data.csv
INFO - Loaded [Y] rephrased SIC descriptions from [package_path]/example_rephrased_sic_data.csv
```

### Data Source Comparison

| Aspect | Package Data (Default) |
|--------|----------------------|
| **Size** | Small (138 lookup, 28 rephrase) |
| **Coverage** | Agricultural SIC codes (01xxx series) |
| **Use Case** | Development, testing, examples |
| **Performance** | Fast loading, small memory footprint |
| **Maintenance** | Automatically updated with package |

### Troubleshooting Data Loading

#### **Common Issues and Solutions**

1. **"File not found" errors**
   - Verify the file paths in environment variables
   - Check file permissions
   - Ensure files exist in the specified locations

2. **Package data not loading**
   - Verify `sic-classification-library` package is installed
   - Check package installation path
   - Ensure package data files are accessible

3. **Mixed configuration not working**
   - Note: Environment variables are no longer used for data loading
   - The API always uses packaged example data by default
   - Review API logs for data loading confirmations

4. **Classification endpoint failing**
   - Ensure vector store service is running
   - Check vector store connectivity
   - Verify data loading completed successfully

#### **Verification Commands**

```bash
# Check current data source configuration
curl -X GET "http://localhost:8080/v1/survey-assist/config"

# Verify SIC lookup is working
curl -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=test"

# Test classification endpoint
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{"llm": "gemini", "type": "sic", "job_title": "Test", "job_description": "Test description"}'

# Check vector store status
curl -X GET "http://localhost:8088/v1/sic-vector-store/status"
```

### Best Practices

1. **Development Environment**: Use package data for quick setup and testing
2. **Production Environment**: Use local data for full classification coverage
3. **Testing**: Test both configurations to ensure flexibility
4. **Monitoring**: Watch logs to confirm data source selection
5. **Documentation**: Document your data source configuration for team members

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
