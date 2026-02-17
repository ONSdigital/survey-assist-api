# Survey Assist API Guide

## Overview

The Survey Assist API is a FastAPI-based service that provides endpoints for industrial classification and data storage. This guide provides detailed information about the API's features, setup, and usage.

## Architecture

The API is built using:
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **SIC Classification Library**: Core classification functionality
- **Vector Store Service**: Embeddings and semantic search capabilities
- **Firestore**: Google Cloud Firestore for storing results and feedback (optional, requires `FIRESTORE_DB_ID`)

**Important Notes**:
- **SOC Classification**: Currently a placeholder implementation. Requests with `type="soc"` or `type="sic_soc"` will return placeholder SOC results. Full SOC classification support is planned for future releases.
- **Firestore**: Result and feedback endpoints require `FIRESTORE_DB_ID` to be set. If not configured, these endpoints will return 503 errors.

## API Endpoints

### Configuration Endpoint
- **Path**: `/v1/survey-assist/config`
- **Method**: GET
- **Description**: Returns the current configuration settings including:
  - LLM model configuration (`llm_model`)
  - Vector store embedding model (`embedding_model`)
  - Data store settings (`data_store`)
  - Firestore database ID (`firestore_database_id`)
  - Classification prompts (per version)
  - Version-specific settings
  - Actual prompt used by the LLM (`actual_prompt`)
- **Response Example**:
  ```json
  {
    "llm_model": "gemini-2.5-flash",
    "embedding_model": "all-MiniLM-L6-v2",
    "data_store": "Firestore",
    "firestore_database_id": "your-database-id",
    "actual_prompt": "Sample SIC classification prompt for testing purposes",
    "v1v2": {
      "classification": [
        {
          "type": "sic",
          "prompts": [
            { 
              "name": "SA_SIC_PROMPT_RAG", 
              "text": "You are a conscientious classification assistant... [full prompt text]" 
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
              "text": "You are a conscientious classification assistant... [full prompt text]" 
            },
            { 
              "name": "SIC_PROMPT_UNAMBIGUOUS", 
              "text": "You are a conscientious classification assistant... [full prompt text]" 
            }
          ]
        }
      ]
    }
  }
  ```
  
  **Note**: The `text` field in prompts contains the full prompt template text, not placeholder text. The `embedding_model` is retrieved from the vector store service. The `actual_prompt` field contains a sample/fallback text.

### Classification Endpoint
- **Path**: `/v1/survey-assist/classify`
- **Method**: POST
- **Description**: Classifies job titles and descriptions into SIC or SOC codes using vector store similarity search and LLM models. Returns a generic response format that supports both SIC and SOC classification types.
- **Request Body**:
  - `llm` (required): The LLM model to use ("chat-gpt" or "gemini"). Note: The API currently uses "gemini-2.5-flash" regardless of this value.
  - `type` (required): Type of classification ("sic", "soc", or "sic_soc")
  - `job_title` (required): Survey response for Job Title
  - `job_description` (required): Survey response for Job Description
  - `org_description` (optional): Survey response for Organisation/Industry Description
  - `options` (optional): Classification options object:
    - `sic` (optional): SIC-specific options:
      - `rephrased` (boolean, default: true): Whether to apply rephrasing to SIC classification results
    - `soc` (optional): SOC-specific options:
      - `rephrased` (boolean, default: true): Whether to apply rephrasing to SOC classification results (not yet implemented)
- **Response**: Returns a generic classification response with the following structure:
  - `requested_type` (string): The type of classification that was requested ("sic", "soc", or "sic_soc")
  - `results` (array): List of classification results, each containing:
    - `type` (string): The classification type ("sic" or "soc")
    - `classified` (boolean): Whether the input could be definitively classified
    - `followup` (string, optional): Additional question to help classify (only present if classified=false)
    - `code` (string, optional): The classification code (only present if classified=true)
    - `description` (string, optional): The classification description (only present if classified=true)
    - `candidates` (array): List of potential classification candidates with:
      - `code` (string): The classification code
      - `descriptive` (string): The classification description
      - `likelihood` (number): Confidence score between 0 and 1
    - `reasoning` (string): Reasoning behind the classification
  - `meta` (object, optional): Response metadata, only included when `options` were provided in the request:
    - `llm` (string): The LLM model used
    - `applied_options` (object): The options that were applied:
      - `sic` (object, optional): Applied SIC options
      - `soc` (object, optional): Applied SOC options

**Note**: SOC classification is currently a placeholder implementation. Requests with `type="soc"` or `type="sic_soc"` will return a placeholder SOC result.

The classification process works as follows:
1. The input text is used to search the vector store for a list of candidate SIC codes.
2. The LLM first attempts to find an **unambiguous** classification from the candidates.
3. If a definitive SIC code is found, the API returns a response with `classified: true` and the found code. The `followup` field will be `null`.
4. If the result is ambiguous and a definitive code cannot be determined, the LLM then formulates a **follow-up question** to gather more information from the user.
5. In this case, the API returns a response with `classified: false`, no code/description, and the `followup` question populated.


### Result Endpoints

#### Store Result
- **Path**: `/v1/survey-assist/result`
- **Method**: POST
- **Description**: Stores classification results in Firestore for later retrieval and analysis. Requires `FIRESTORE_DB_ID` environment variable to be set.
- **Request Body**:
  ```json
  {
    "survey_id": "test-survey-123",
    "case_id": "test-case-456",
    "wave_id": "wave-789",
    "user": "test.userSA187",
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
- **Response**: Returns stored result information with Firestore document ID:
  ```json
  {
    "message": "Result stored successfully",
    "result_id": "abc123def456ghi789"
  }
  ```
  Note: `result_id` is a Firestore document ID (auto-generated, 20-character alphanumeric string).

#### Get Result
- **Path**: `/v1/survey-assist/result`
- **Method**: GET
- **Description**: Retrieves a stored classification result from Firestore by document ID. Requires `FIRESTORE_DB_ID` environment variable to be set.
- **Query Parameters**:
  - `result_id` (required): The Firestore document ID of the result to retrieve (e.g., "abc123xyz456def789gh")
- **Response**: Returns the stored result in the same format as the POST request body.

#### List Results
- **Path**: `/v1/survey-assist/results`
- **Method**: GET
- **Description**: Lists stored classification results from Firestore filtered by survey_id, wave_id, and optionally case_id. Requires `FIRESTORE_DB_ID` environment variable to be set.
- **Query Parameters**:
  - `survey_id` (required): Survey identifier to filter by
  - `wave_id` (required): Wave identifier to filter by
  - `case_id` (optional): Case identifier to filter by. If omitted, returns all results for the survey/wave.
- **Response**: Returns a list of matching results with their Firestore document IDs:
  ```json
  {
    "results": [
      {
        "survey_id": "test-survey-123",
        "case_id": "test-case-456",
        "wave_id": "wave-789",
        "user": "test.userSA187",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:05:00Z",
        "responses": [...],
        "document_id": "abc123def456ghi789"
      }
    ],
    "count": 1
  }
  ```

### Feedback Endpoints

#### Store Feedback
- **Path**: `/v1/survey-assist/feedback`
- **Method**: POST
- **Description**: Stores respondent feedback data in Firestore. Requires `FIRESTORE_DB_ID` environment variable to be set so that the Firestore client can be initialised.
- **Storage details**:
  - Feedback is stored in the `survey_feedback` collection
  - Each request becomes a single document; the returned `feedback_id` is the Firestore document ID
  - The combination of `case_id`, `person_id`, and `wave_id` is logged as a `feedback_body_id` for traceability in logs
- **Request Body**:
  ```json
  {
    "case_id": "0710-25AA-XXXX-YYYY",
    "person_id": "000001_01",
    "survey_id": "survey_123",
    "wave_id": "wave_456",
    "questions": [
      {
        "response": "Very satisfied",
        "response_name": "satisfaction_question",
        "response_options": [
          "Very satisfied",
          "Satisfied",
          "Neutral",
          "Dissatisfied",
          "Very dissatisfied"
        ]
      },
      {
        "response": "The survey was easy to complete and helpful.",
        "response_name": "comments_question",
        "response_options": null
      }
    ]
  }
  ```
- **Validation rules** (enforced by the API):
  - `case_id`, `person_id`, `survey_id`, `wave_id`, and `questions` are required
  - Each question must include `response` and `response_name`
  - `response_options` (when present) must be an array of strings; passing any other type will result in a 422 validation error
  - An empty `questions` array is allowed and will still be stored successfully
- **Response**: Returns feedback storage confirmation:
  ```json
  {
    "message": "Feedback stored successfully",
    "feedback_id": "fb123def456ghi789"
  }
  ```
  If Firestore is not configured correctly (for example, `FIRESTORE_DB_ID` is missing), the endpoint will fail with a server error when it attempts to initialise the Firestore client. See `docs/gcp_deployment.md` for full details of the required environment variables in deployed environments.

#### Get Feedback
- **Path**: `/v1/survey-assist/feedback`
- **Method**: GET
- **Description**: Retrieves a stored feedback result from Firestore by document ID. Requires `FIRESTORE_DB_ID` environment variable to be set.
- **Query Parameters**:
  - `feedback_id` (required): The Firestore document ID of the feedback to retrieve (for example, `"fb123def456ghi789"`)
- **Response**: Returns the stored feedback in the same format as the POST request body (without `feedback_id`), including `case_id`, `person_id`, `survey_id`, `wave_id`, and `questions`.

#### List Feedbacks
- **Path**: `/v1/survey-assist/feedbacks`
- **Method**: GET
- **Description**: Lists stored feedback results from Firestore filtered by `survey_id`, `wave_id`, and optionally `case_id`. Requires `FIRESTORE_DB_ID` environment variable to be set.
- **Query Parameters**:
  - `survey_id` (required): Survey identifier to filter by
  - `wave_id` (required): Wave identifier to filter by
  - `case_id` (optional): Case identifier to filter by. If omitted, returns all feedback for the survey/wave.
- **Response**: Returns a list of matching feedback results with their Firestore document IDs:
  ```json
  {
    "results": [
      {
        "case_id": "0710-25AA-XXXX-YYYY",
        "person_id": "000001_01",
        "survey_id": "survey_123",
        "wave_id": "wave_456",
        "questions": [
          {
            "response": "Very satisfied",
            "response_name": "satisfaction_question",
            "response_options": [
              "Very satisfied",
              "Satisfied",
              "Neutral",
              "Dissatisfied",
              "Very dissatisfied"
            ]
          }
        ],
        "document_id": "fb123def456ghi789"
      }
    ],
    "count": 1
  }
  ```

### Example Usage

#### Classification
```bash
# Basic SIC classification
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Electrician",
    "job_description": "Installing and maintaining electrical systems",
    "org_description": "Electrical contracting company"
  }'

# SIC classification with rephrasing disabled
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Electrician",
    "job_description": "Installing and maintaining electrical systems",
    "org_description": "Electrical contracting company",
    "options": {
      "sic": {
        "rephrased": false
      }
    }
  }'
```

**Expected response format (without options, no meta field):**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "43210",
      "description": "Electrical installation",
      "candidates": [
        {
          "code": "43210",
          "descriptive": "Electrical installation",
          "likelihood": 0.99
        }
      ],
      "reasoning": "The respondent data clearly states 'Electrical contracting'..."
    }
  ]
}
```

**Expected response format (with options, includes meta field):**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "43210",
      "description": "Electrical installation",
      "candidates": [
        {
          "code": "43210",
          "descriptive": "Electrical installation",
          "likelihood": 0.99
        }
      ],
      "reasoning": "The respondent data clearly states 'Electrical contracting'..."
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {
        "rephrased": false
      },
      "soc": {}
    }
  }
}
```

#### Result Storage and Retrieval
```bash
# Store a result
curl -X POST "http://localhost:8080/v1/survey-assist/result" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": "test-survey-123",
    "case_id": "test-case-456",
    "wave_id": "wave-789",
    "user": "test.userSA187",
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

# Retrieve a result by document ID
curl -X GET "http://localhost:8080/v1/survey-assist/result?result_id=abc123def456ghi789"

# List results for a survey/wave
curl -X GET "http://localhost:8080/v1/survey-assist/results?survey_id=test-survey-123&wave_id=wave-789"

# List results for a specific case
curl -X GET "http://localhost:8080/v1/survey-assist/results?survey_id=test-survey-123&wave_id=wave-789&case_id=test-case-456"
```

#### Feedback
```bash
# Store feedback
curl -X POST "http://localhost:8080/v1/survey-assist/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "0710-25AA-XXXX-YYYY",
    "person_id": "000001_01",
    "survey_id": "survey_123",
    "wave_id": "wave_456",
    "questions": [
      {
        "response": "Very satisfied",
        "response_name": "satisfaction_question",
        "response_options": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"]
      }
    ]
  }'
```

### SIC Lookup Endpoint
- **Path**: `/v1/survey-assist/sic-lookup`
- **Method**: GET
- **Parameters**:
  - `description` (required): The business description to look up
  - `similarity` (optional, default: false): Boolean flag for similarity search
- **Description**: Performs SIC code lookup with two modes:
  - Exact match (`similarity=false`): Returns exact matches only
  - Similarity search (`similarity=true`): Returns similar matches using fuzzy matching
- **Data Sources**: 
  - **Default**: Uses package example data from `sic-classification-library` package
  - **Custom**: Can be overridden by setting `SIC_LOOKUP_DATA_PATH` environment variable
- **Response Structure**: The response structure varies based on whether a match is found and whether similarity search is used:
  
  **When a match is found (exact match):**
  ```json
  {
    "code": "43210",
    "description": "electrical installation",
    "code_meta": null,
    "code_division": null,
    "code_division_meta": null
  }
  ```
  
  **When no match is found (exact match):**
  ```json
  {
    "description": "electrical installation",
    "code": null,
    "code_meta": null,
    "code_division": null,
    "code_division_meta": null
  }
  ```
  
  **When similarity search is enabled (`similarity=true`):**
  ```json
  {
    "description": "electrical installation",
    "code": null,
    "code_meta": null,
    "code_division": null,
    "code_division_meta": null,
    "potential_matches": {
      "descriptions_count": 0,
      "descriptions": [],
      "codes_count": 0,
      "codes": [],
      "divisions_count": 0,
      "divisions": []
    }
  }
  ```
  
  **Note**: The `description` field in the response contains the input description (lowercased). When a match is found, `code` contains the SIC code. The `potential_matches` object is only present when `similarity=true` and contains arrays of potential matches.

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

**Note**: The API requires GCP credentials to start up due to LLM initialisation at startup.

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

**Expected response format (no meta field since no options provided):**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "01500",
      "description": "Mixed farming",
      "candidates": [
        {
          "code": "01500",
          "descriptive": "Crop and livestock farm",
          "likelihood": 0.99
        }
      ],
      "reasoning": "The respondent data states 'Agricultural farm' and 'Grows crops and raises livestock'..."
    }
  ]
}
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

**Data Loading Behaviour**:
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

| Variable | Description | Example | Default Behaviour | Required For |
|----------|-------------|---------|------------------|--------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account key | `/app/service-account-key.json` | None | LLM functionality (Gemini) |
| `GCP_PROJECT_ID` | Google Cloud Project ID | `my-project-id` | None | Firestore (optional, uses default project if not set) |
| `FIRESTORE_DB_ID` | Firestore Database ID | `my-database-id` | None | Result and feedback endpoints |
| `SIC_VECTOR_STORE` | Vector store service URL | `http://<host-ip-address>:8088` | `http://localhost:8088` | Classification and embeddings endpoints |
| `SIC_LOOKUP_DATA_PATH` | Path to SIC lookup data file (optional override) | `data/sic_knowledge_base_utf8.csv` | Uses `example_sic_lookup_data.csv` from `industrial_classification.data` package | None (optional override) |
| `SIC_REPHRASE_DATA_PATH` | Path to SIC rephrase data file (optional override) | `data/sic_rephrased_descriptions_2025_02_03.csv` | Uses `example_rephrased_sic_data.csv` from `industrial_classification.data` package | None (optional override) |
| `PORT` | API port | `8080` | `8080` | None (uvicorn default) |

**Important Notes**:
- If `FIRESTORE_DB_ID` is not set, the Firestore client will not be initialised and result/feedback endpoints will return 503 errors.
- If `GCP_PROJECT_ID` is not set, Firestore will attempt to use the default project from your GCP credentials.
- The API uses package example data by default for SIC lookup and rephrase. Set environment variables only if you need to override with custom datasets.

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

The API loads data files from configurable paths. By default, it uses example data from the `industrial_classification.data` package:

- **SIC Lookup Data**: Defaults to `example_sic_lookup_data.csv` from the package
- **SIC Rephrase Data**: Defaults to `example_rephrased_sic_data.csv` from the package

You can override these defaults by setting environment variables:
- **SIC Lookup Data**: `SIC_LOOKUP_DATA_PATH` (e.g., `data/sic_knowledge_base_utf8.csv` if you have custom data)
- **SIC Rephrase Data**: `SIC_REPHRASE_DATA_PATH` (e.g., `data/sic_rephrased_descriptions_2025_02_03.csv` if you have custom data)

**Note**: If you're using Docker and want to use custom data files, they must be included in the Docker image during the build process (copied into the `data/` folder before building).

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

**Note**: The API uses package example data by default. Environment variables are optional and only needed if you want to override with custom datasets.


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
# Set environment variables to use local data
export SIC_LOOKUP_DATA_PATH=data/sic_knowledge_base_utf8.csv
export SIC_REPHRASE_DATA_PATH=data/sic_rephrased_descriptions_2025_02_03.csv

# Test SIC lookup with local data
curl -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=electrician"

# Expected response: SIC code 43210 with description "Electrical installation"
```

#### **Test 3: Mixed Configuration**
```bash
# Use local lookup data but package rephrase data
export SIC_LOOKUP_DATA_PATH=data/sic_knowledge_base_utf8.csv
# SIC_REPHRASE_DATA_PATH not set, so package data will be used

# Test classification with mixed data sources
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
   - Verify environment variables are set correctly
   - Check that file paths are accessible from the container/process
   - Review API logs for data loading confirmations
   - Ensure paths are relative to the working directory or absolute paths

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
