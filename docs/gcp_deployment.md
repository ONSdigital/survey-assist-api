# Survey Assist API - GCP Deployment Guide

This document provides information about deploying the Survey Assist API to Google Cloud Platform (GCP) Cloud Run.

## Overview

The Survey Assist API uses **automated CI/CD pipelines** for all deployments to GCP Cloud Run. All deployments are handled automatically by Google Cloud Build pipelines.

### Deployment Summary

| Environment | Deployment Method | Pipeline File |
|------------|------------------|---------------|
| Development/Sandbox | Automated via Cloud Build | `cicd/cloudbuild_dev_and_sandbox.yaml` |
| Pre-Production | Automated promotion pipeline | `cicd/cloudbuild_promote_preprod.yaml` |
| Production | Automated (via promotion pipeline) | `cicd/cloudbuild_promote_preprod.yaml` |

**What the CI/CD Pipeline Does:**
1. Runs full test suite with coverage checks (80% minimum)
2. Downloads data files from Google Cloud Storage
3. Builds Docker image
4. Pushes to Artifact Registry
5. Deploys to Cloud Run
6. Runs smoke tests

## Automated CI/CD Deployment

All deployments are handled automatically by CI/CD pipelines. The pipelines handle testing, building, pushing, and deploying the application.

### Development and Sandbox Environments

Deployment to development and sandbox environments is automated via Google Cloud Build. The pipeline is triggered automatically and performs the following steps:

1. **Run Tests**: Executes the full test suite with coverage requirements (80% minimum)
2. **Build Docker Image**: Builds the Docker image with data files from Google Cloud Storage
3. **Push to Artifact Registry**: Pushes the image to Google Artifact Registry (GAR) with both `latest` and `SHORT_SHA` tags
4. **Deploy to Cloud Run**: Deploys the image to the target Cloud Run service
5. **Run Smoke Tests**: Executes smoke tests against the deployed service

**Pipeline Configuration**: `cicd/cloudbuild_dev_and_sandbox.yaml`

**Key Steps**:
- Downloads SIC lookup and rephrase CSV files from Google Cloud Storage (`$_SIC_LOOKUP_CSV`, `$_SIC_REPHRASE_CSV`)
- Builds Docker image tagged with both `latest` and commit SHA
- Deploys to Cloud Run using the SHA-tagged image
- Runs smoke tests using service account impersonation

### Pre-Production Promotion

Promotion to pre-production is automated via a separate Cloud Build pipeline:

1. **Pull Dev Image**: Pulls the development image by SHA tag
2. **Tag as Release**: Tags the image with a release tag name
3. **Push to Release Registry**: Pushes to the releases Artifact Registry repository
4. **Deploy to Pre-Production**: Deploys to the pre-production Cloud Run service
5. **Run Smoke Tests**: Executes smoke tests against the pre-production environment

**Pipeline Configuration**: `cicd/cloudbuild_promote_preprod.yaml`

**Trigger**: Manual promotion via Cloud Build with a release tag name

### Local Smoke Test Execution

You can run smoke tests locally against deployed environments:

```bash
# Run smoke tests against dev environment
./cicd/run_smoke_tests.sh dev

# Run smoke tests against sandbox environment
./cicd/run_smoke_tests.sh sandbox
```

The script automatically:
- Retrieves the API URL from Parameter Manager (if `SURVEY_ASSIST_API_URL` not set)
- Generates a Google Identity Token (if `SA_ID_TOKEN` not set)
- Runs the smoke test suite

**Prerequisites**:
- `gcloud` CLI authenticated
- Access to the target GCP project
- `pytest` and dependencies installed

## Configuration Reference

### Environment Variables

The CI/CD pipeline configures the following environment variables for the Cloud Run service:

**Required:**
- `SIC_VECTOR_STORE`: URL of the SIC classification vector store service (required for classification functionality)
- `FIRESTORE_DB_ID`: Firestore Database ID (required for result and feedback endpoints)

**Optional:**
- `GCP_PROJECT_ID`: Google Cloud Project ID (optional, uses default project if not set)
- `SIC_LOOKUP_DATA_PATH`: Path to custom SIC lookup data file (optional, defaults to package example data)
- `SIC_REPHRASE_DATA_PATH`: Path to custom SIC rephrase data file (optional, defaults to package example data)

**Data Loading Behavior**:
- **Package Data (default)**: The API uses example data from the `industrial_classification.data` package when no custom data paths are specified
- **Custom Data Sources**: Can be specified via `SIC_LOOKUP_DATA_PATH` and `SIC_REPHRASE_DATA_PATH` environment variables
- **Firestore**: If `FIRESTORE_DB_ID` is not set, result and feedback endpoints will return 503 errors

**Note**: The `SIC_VECTOR_STORE` URL is configured in the CI/CD pipeline. To find the vector store service URL:
```bash
gcloud run services list --project={PROJECT_ID} --region={REGION} | grep -i vector
```

### Service Account Configuration

The Cloud Run service requires a service account with the following IAM roles:
- `roles/run.invoker` (for service-to-service communication with vector store)
- `roles/iam.serviceAccountTokenCreator` (for generating ID tokens)
- Firestore access (if using Firestore features)

The service account is configured in the CI/CD pipeline.

## Authentication Note

**All testing is done through the API Gateway using signed JWT tokens for authentication.** We never test Cloud Run services directly. Google Identity tokens (`gcloud auth print-identity-token`) cannot be used. See the [JWT Token Generation](#jwt-token-generation-process) section below for details on creating proper JWT tokens.

## Testing Deployed Services

**Important**: All testing is done through the API Gateway using signed JWT tokens for authentication. See the [JWT Token Generation](#jwt-token-generation-process) section below for details on creating proper JWT tokens.

```bash
# Test endpoints with authentication through API Gateway
# Replace {API_GATEWAY_URL} with your actual API Gateway hostname

# Test config endpoint
curl -H "Authorization: Bearer ${JWT_TOKEN}" "https://{API_GATEWAY_URL}/v1/survey-assist/config"

# Test SIC lookup endpoint
curl -H "Authorization: Bearer ${JWT_TOKEN}" "https://{API_GATEWAY_URL}/v1/survey-assist/sic-lookup?description=electrical%20installation"

# Test classify endpoint
curl -X POST -H "Authorization: Bearer ${JWT_TOKEN}" -H "Content-Type: application/json" -d '{"llm": "gemini", "type": "sic", "job_title": "Electrician", "job_description": "Installing electrical systems", "org_description": "Electrical contracting company"}' "https://{API_GATEWAY_URL}/v1/survey-assist/classify"
```

## Service-to-Service Authentication

The Survey Assist API is configured to communicate securely with other Cloud Run services (such as the SIC Classification Vector Store) using Google Cloud's service-to-service authentication with ID tokens.

### Authentication Implementation

The API uses **Application Default Credentials (ADC)** to automatically obtain and use Google Cloud ID tokens for service-to-service communication:

- **ID Token Generation**: Uses `google.oauth2.id_token.fetch_id_token()` with proper audience validation
- **Automatic Authentication**: Leverages the service account's identity to authenticate requests
- **Secure Communication**: All inter-service requests include `Authorization: Bearer <id_token>` headers

### Required Dependencies

The following Google Cloud dependencies are included in `pyproject.toml`:

```toml
google-cloud-logging = "^3.9.0"
google-auth = "^2.28.0"
```

### Environment Configuration

The `SIC_VECTOR_STORE` environment variable is configured by the CI/CD pipeline to enable secure communication with the vector store service.

### Service Account Permissions

The `survey-assist-api` service account requires the following IAM roles for service-to-service communication:

- **Cloud Run Invoker** (`roles/run.invoker`) on the vector store service
- **IAM Service Account Token Creator** (`roles/iam.serviceAccountTokenCreator`) for generating ID tokens

These permissions are configured as part of the infrastructure setup.

### Testing Service-to-Service Communication

Test the complete end-to-end flow including service-to-service authentication:

```bash
# Test with complete request including org_description
curl -X POST \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Electrician",
    "job_description": "I install and maintain electrical systems and wiring",
    "org_description": "Electrical installation and maintenance services"
  }' \
  "https://{API_GATEWAY_URL}/v1/survey-assist/classify"
```

**Expected Response**: Successful SIC classification with proper authentication between services.

**Data Loading Verification**: The deployed service will use package example data by default, or custom datasets if `SIC_LOOKUP_DATA_PATH` and `SIC_REPHRASE_DATA_PATH` environment variables are set. You can verify this by checking the startup logs for data loading messages showing which data source was used.

#### Complete Working Example

Here's a complete example of generating and using a JWT token:

```bash
# 1. Create payload with current timestamps
echo '{"iat":' $(date +%s) ',"exp":' $(( $(date +%s) + 3600 )) ',"iss":"<your-service-account-email>","aud":"<your-api-gateway-hostname>","sub":"<your-service-account-email>","email":"<your-service-account-email>"}' > payload.json

# 2. Sign the JWT
gcloud iam service-accounts sign-jwt \
  --iam-account=<your-service-account-email> \
  payload.json \
  output.txt

# 3. Use the token
TOKEN=$(cat output.txt)

# 4. Test the API
curl -H "Authorization: Bearer ${TOKEN}" \
  "https://<api-gateway-hostname>/v1/survey-assist/config"
```

## API Gateway Configuration

The API Gateway is configured separately from the Cloud Run deployment. The following steps are for initial API Gateway setup:

### Fix Swagger2 Compatibility Issues

The original spec contains OpenAPI 3.0 features that aren't supported by API Gateway. Fix these issues:

```bash
# Remove examples fields (not supported in Swagger 2.0)
jq 'del(.. | select(type == "object" and has("examples")).examples)' swagger2_original.json > swagger2_fixed.json

# Remove anyOf fields (not supported in Swagger 2.0)
jq 'del(.. | select(type == "object" and has("anyOf")).anyOf)' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json

# Add Google Cloud API Gateway extensions for JWT authentication
jq '. + {"x-google-backend": {"address": "{SURVEY_ASSIST_API_URL}", "protocol": "h2", "path_translation": "APPEND_PATH_TO_ADDRESS"}, "host": "{API_GATEWAY_HOSTNAME}", "securityDefinitions": {"backend_api_access": {"authorizationUrl": "", "flow": "implicit", "type": "oauth2", "x-google-issuer": "{SERVICE_ACCOUNT_EMAIL}", "x-google-jwks_uri": "https://www.googleapis.com/robot/v1/metadata/x509/{SERVICE_ACCOUNT_EMAIL}", "x-google-audiences": "{API_GATEWAY_HOSTNAME}"}}, "security": [{"backend_api_access": []}]}' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json

# Note: Replace placeholders with actual values:
# {SURVEY_ASSIST_API_URL}: Your Cloud Run service URL
# {API_GATEWAY_HOSTNAME}: Your API Gateway hostname
# {SERVICE_ACCOUNT_EMAIL}: Service account that will sign JWTs
```

### Deploy the Fixed Specification

```bash
# Create new API config with fixed spec
gcloud api-gateway api-configs create survey-assist-api-config-v3 \
  --api=survey-assist-api \
  --openapi-spec=swagger2_fixed.json \
  --project={PROJECT_ID} \
  --backend-auth-service-account={BACKEND_AUTH_SERVICE_ACCOUNT}
```

### Update the Gateway

```bash
# Update existing gateway to use new config
gcloud api-gateway gateways update survey-assist-api-gw \
  --api-config=survey-assist-api-config-v3 \
  --api=survey-assist-api \
  --location={REGION} \
  --project={PROJECT_ID} \
  --backend-auth-service-account={BACKEND_AUTH_SERVICE_ACCOUNT}
```

### Test API Gateway Endpoints

**Important**: API Gateway requires signed JWT tokens, not Google Identity tokens. See the [API Gateway Authentication with JWT Tokens](#api-gateway-authentication-with-jwt-tokens) section for details on generating proper JWT tokens.

```bash
# Get the current gateway URL
GATEWAY_URL="$(gcloud api-gateway gateways describe survey-assist-api-gw --location={REGION} --project={PROJECT_ID} --format='value(defaultHostname)')"

# First, generate a signed JWT token (see JWT authentication section above)
# Then test endpoints with the JWT token:

# Test config endpoint
curl --header "Authorization: Bearer ${JWT_TOKEN}" \
  "https://$GATEWAY_URL/v1/survey-assist/config"

# Test embeddings endpoint
curl --header "Authorization: Bearer ${JWT_TOKEN}" \
  "https://$GATEWAY_URL/v1/survey-assist/embeddings"

# Test SIC lookup endpoint (uses package data by default)
curl --header "Authorization: Bearer ${JWT_TOKEN}" \
  "https://$GATEWAY_URL/v1/survey-assist/sic-lookup?description=electrical%20installation"

# Test classify endpoint (uses package data by default)
curl -X POST --header "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"llm":"gemini","type":"sic","job_title":"Electrician","job_description":"I install and maintain electrical systems and wiring","org_description":"Electrical installation and maintenance services"}' \
  "https://$GATEWAY_URL/v1/survey-assist/classify"

# Test classify endpoint with rephrase toggle (SIC rephrasing enabled)
curl -X POST --header "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"llm":"gemini","type":"sic","job_title":"Farmer","job_description":"Growing cereals and crops","org_description":"Agricultural farm","options":{"sic":{"rephrased":true}}}' \
  "https://$GATEWAY_URL/v1/survey-assist/classify"

# Test classify endpoint with rephrase toggle (SIC rephrasing disabled)
curl -X POST --header "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"llm":"gemini","type":"sic","job_title":"Farmer","job_description":"Growing cereals and crops","org_description":"Agricultural farm","options":{"sic":{"rephrased":false}}}' \
  "https://$GATEWAY_URL/v1/survey-assist/classify"

# Test result endpoint (requires FIRESTORE_DB_ID to be set)
curl -X POST --header "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"survey_id":"test-123","case_id":"test-456","wave_id":"wave-789","user":"test.userSA187","time_start":"2024-01-01T10:00:00Z","time_end":"2024-01-01T10:05:00Z","responses":[]}' \
  "https://$GATEWAY_URL/v1/survey-assist/result"

# Test feedback endpoint (requires FIRESTORE_DB_ID to be set)
curl -X POST --header "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"case_id":"0710-25AA-XXXX-YYYY","person_id":"000001_01","survey_id":"survey_123","wave_id":"wave_456","questions":[{"response":"Very satisfied","response_name":"satisfaction_question","response_options":["Very satisfied","Satisfied","Neutral","Dissatisfied","Very dissatisfied"]}]}' \
  "https://$GATEWAY_URL/v1/survey-assist/feedback"

# Test authentication enforcement (should return 401)
curl "https://$GATEWAY_URL/v1/survey-assist/config"
```

**Expected Responses**:
- **Config**: Returns LLM model, embedding model, Firestore database ID, and prompt configurations
- **Data Loading**: Service uses package example data by default, or custom data if `SIC_LOOKUP_DATA_PATH` and `SIC_REPHRASE_DATA_PATH` environment variables are set
- **Embeddings**: Returns vector store status and metadata
- **SIC Lookup**: Returns SIC code lookup results
- **Classify**: Returns generic classification response with SIC/SOC results
  - **Rephrasing enabled**: `candidates[].descriptive` shows user-friendly descriptions (e.g., "Crop growing", "Dairy farming")
  - **Rephrasing disabled**: `candidates[].descriptive` shows original SIC descriptions
  - **Main description**: Always shows official SIC code description
  - **Response format**: Generic format with `requested_type`, `results` array, and optional `meta` field
- **Result**: Returns confirmation with Firestore document ID (requires `FIRESTORE_DB_ID`)
- **Feedback**: Returns confirmation with Firestore document ID (requires `FIRESTORE_DB_ID`)
- **Unauthenticated**: Returns `{"code":401,"message":"Jwt is missing"}`
**API Gateway Endpoints:**
All endpoints are accessible via the API Gateway at `{API_GATEWAY_URL}/v1/survey-assist/`:

- **Config**: `GET /config` - Get API configuration and prompt settings
- **Embeddings**: `GET /embeddings` - Get vector store status and metadata
- **SIC Lookup**: `GET /sic-lookup` - Lookup SIC codes by description
- **Classification**: `POST /classify` - Classify job descriptions to SIC/SOC codes (generic response format)
- **Results**:
  - `POST /result` - Store survey interaction results (requires `FIRESTORE_DB_ID`)
  - `GET /result` - Retrieve a stored result by document ID (requires `FIRESTORE_DB_ID`)
  - `GET /results` - List results filtered by survey_id, wave_id, and optionally case_id (requires `FIRESTORE_DB_ID`)
- **Feedback**:
  - `POST /feedback` - Store feedback data (requires `FIRESTORE_DB_ID`)
  - `GET /feedback` - Retrieve feedback by ID (requires `FIRESTORE_DB_ID`)
  - `GET /feedbacks` - List feedback by survey_id, wave_id, and optionally case_id (requires `FIRESTORE_DB_ID`)

## API Gateway Authentication with JWT Tokens

### Important: JWT vs Google Identity Tokens

**API Gateway requires signed JWT tokens, NOT Google Identity tokens.** This is a critical distinction:

- **❌ Google Identity Token** (`gcloud auth print-identity-token`): This is a Google-generated token that identifies the user but cannot be used for API Gateway authentication
- **✅ Signed JWT Token**: This is a custom JWT token that must be signed by the service account specified in the Swagger spec's `x-google-issuer` field

### JWT Token Generation Process

To authenticate with API Gateway, you must generate a signed JWT token:

#### Prerequisites: Get Your API Gateway Details

Before generating the JWT token, you need to know your API Gateway hostname and service account:

```bash
# 1. List your API Gateways
gcloud api-gateway gateways list --project={PROJECT_ID}

# 2. Get the API Gateway hostname
gcloud api-gateway gateways describe {GATEWAY_ID} \
  --location={REGION} \
  --project={PROJECT_ID} \
  --format='value(defaultHostname)'

# 3. Get the service account from the API config

- **API Gateway hostname**: `your-gateway-name-xxxxx.nw.gateway.dev`
- **Service account**: `your-service-account@your-project.iam.gserviceaccount.com`

#### Quick 3-Step Process

1. **Create payload** - JSON with timestamps, service account email, and API Gateway hostname
2. **Sign with service account** - Use `gcloud iam service-accounts sign-jwt --iam-account={SERVICE_ACCOUNT_EMAIL} payload.json output.txt`
3. **Use token** - Read from `output.txt` and include in `Authorization: Bearer ${TOKEN}` header

#### 1. Create JWT Payload

Create a `payload.json` file with the required claims:

```json
{
  "iat": <current_unix_timestamp>,
  "exp": <current_unix_timestamp + 3600>,
  "iss": "<your-service-account-email>",
  "aud": "<your-api-gateway-hostname>",
  "sub": "<your-service-account-email>",
  "email": "<your-service-account-email>"
}
```

**Required fields:**
- `iat`: Issued at timestamp (current Unix timestamp in seconds)
- `exp`: Expiration timestamp (current Unix timestamp + 3600 seconds = 1 hour from now)
- `iss`: Issuer (service account that will sign the JWT)
- `aud`: Audience (your API Gateway hostname)
- `sub`: Subject (same as issuer)
- `email`: Service account email (same as issuer)

**Quick timestamp generation:**
```bash
# Get current timestamp
echo "Current timestamp: $(date +%s)"

# Create payload with current timestamps
echo '{"iat":' $(date +%s) ',"exp":' $(( $(date +%s) + 3600 )) ',"iss":"<your-service-account-email>","aud":"<your-api-gateway-hostname>","sub":"<your-service-account-email>","email":"<your-service-account-email>"}' > payload.json
```

#### 2. Generate Signed JWT

Use the service account to sign the JWT payload:

```bash
# Sign the JWT using service account impersonation
gcloud iam service-accounts sign-jwt \
  --iam-account=<service-account-email> \
  payload.json \
  output.txt
```

**Prerequisites:**
- The user/service account must have `roles/iam.serviceAccountTokenCreator` on the target service account
- The target service account must be specified in the Swagger spec's `x-google-issuer` field

#### 3. Use JWT Token for Authentication

```bash
# Read the signed JWT token
TOKEN=$(cat output.txt)

# Make authenticated requests
curl --header "Authorization: Bearer ${TOKEN}" \
  "https://<api-gateway-hostname>/v1/survey-assist/config"
```

### Testing API Gateway Endpoints

The API Gateway provides access to all survey-assist-api endpoints with JWT authentication:

**Basic Endpoints**:
```bash
# Configuration endpoint
curl --header "Authorization: Bearer ${TOKEN}" \
  "https://<api-gateway-hostname>/v1/survey-assist/config"

# SIC lookup endpoint (uses package example data by default)
curl --header "Authorization: Bearer ${TOKEN}" \
  "https://<api-gateway-hostname>/v1/survey-assist/sic-lookup?description=electrical%20installation"
```

**Classification Endpoints**:
```bash
# Classification with rephrase enabled (user-friendly descriptions)
curl --header "Authorization: Bearer ${TOKEN}" \
  --header "Content-Type: application/json" \
  --data '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "electrical engineer",
    "job_description": "designing and installing electrical systems",
    "org_description": "electrical contracting company",
    "options": {
      "sic": {
        "rephrased": true
      }
    }
  }' \
  "https://<api-gateway-hostname>/v1/survey-assist/classify"

# Classification with rephrase disabled (original SIC descriptions)
curl --header "Authorization: Bearer ${TOKEN}" \
  --header "Content-Type: application/json" \
  --data '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "electrical engineer",
    "job_description": "designing and installing electrical systems",
    "org_description": "electrical contracting company",
    "options": {
      "sic": {
        "rephrased": false
      }
    }
  }' \
  "https://<api-gateway-hostname>/v1/survey-assist/classify"
```

### Swagger Specification Requirements

For JWT authentication to work, the Swagger spec must include:

```json
{
  "securityDefinitions": {
    "backend_api_access": {
      "authorizationUrl": "",
      "flow": "implicit",
      "type": "oauth2",
      "x-google-issuer": "<service-account-email>",
      "x-google-jwks_uri": "https://www.googleapis.com/robot/v1/metadata/x509/<service-account-email>",
      "x-google-audiences": "<api-gateway-hostname>"
    }
  },
  "security": [
    {
      "backend_api_access": []
    }
  ],
  "x-google-backend": {
    "address": "<cloud-run-service-url>",
    "protocol": "h2",
    "path_translation": "APPEND_PATH_TO_ADDRESS"
  }
}
```

**Critical fields:**
- `x-google-issuer`: Service account that will sign JWTs
- `x-google-audiences`: API Gateway hostname for JWT validation
- `host`: API Gateway hostname
- `protocol: h2`: HTTP/2 protocol for backend communication
- `path_translation: "APPEND_PATH_TO_ADDRESS"`: How API Gateway routes requests

### Testing Authentication

#### Test with Valid JWT Token (should return 200 OK)
```bash
curl --header "Authorization: Bearer ${TOKEN}" \
  "https://<api-gateway-hostname>/v1/survey-assist/config"
```

#### Test without Token (should return 401 Unauthorized)
```bash
curl "https://<api-gateway-hostname>/v1/survey-assist/config"
# Expected: {"message":"Jwt is missing","code":401}
```

### Troubleshooting Common Issues

1. **"Jwt issuer is not configured"**: Check that `x-google-issuer` in Swagger spec matches the service account used to sign JWTs
2. **"Jwt is missing"**: Ensure all endpoints have `security` requirements in the Swagger spec
3. **Authentication bypassed**: Verify the Swagger spec includes all required `x-google-*` fields and proper `securityDefinitions`
4. **Service account mismatch**: The API Gateway config's `gatewayServiceAccount` may differ from the `x-google-issuer` - this can still work if the Swagger spec is properly configured


## Swagger2 Support (August 2025)

The API has been updated to support Swagger2 (OpenAPI v2) for Google Cloud API Gateway compatibility:

### Changes Made
- **Added `fastapi_swagger2` dependency** (v0.2.4)
- **Replaced OpenAPI v3 endpoints** with Swagger2 endpoints
- **Updated documentation URLs** from `/docs` to `/swagger2/docs`

### New Endpoints
- `/swagger2.json` - Swagger2 specification (API Gateway compatible)
- `/swagger2/docs` - Swagger2 UI
- `/swagger2/redoc` - ReDoc for Swagger2

### Breaking Changes
- `/docs`, `/redoc`, `/openapi.json` endpoints removed
- **Documentation URLs updated** - all references changed to `/swagger2/*`

### Testing Swagger2
```bash
# Test new Swagger2 endpoints
curl -H "Authorization: Bearer ${JWT_TOKEN}" \
  "$(gcloud run services describe survey-assist-api --region={REGION} --project={PROJECT_ID} --format='value(status.url)')/swagger2.json"
```

## Key Learnings and Best Practices

### Authentication Success Factors

Based on our deployment experience, the following factors are critical for API Gateway JWT authentication to work:

1. **Complete Swagger Specification**: The spec must include all required fields:
   - `host`: API Gateway hostname
   - `x-google-backend` with `protocol: h2` and `path_translation: "APPEND_PATH_TO_ADDRESS"`
   - Proper `securityDefinitions` with OAuth2 type
   - `x-google-issuer`, `x-google-jwks_uri`, and `x-google-audiences`

2. **JWT Token Requirements**: 
   - Must be signed by the service account specified in `x-google-issuer`
   - Must include all required claims (`iat`, `exp`, `iss`, `aud`, `sub`, `email`)
   - Timestamps must be current (within 1 hour validity)

3. **Service Account Configuration**:
   - The signing service account must have `roles/iam.serviceAccountTokenCreator`
   - Users must have permission to impersonate the signing service account
   - The `x-google-issuer` in Swagger spec must match the signing service account

### Common Pitfalls to Avoid

- ** Using `gcloud auth print-identity-token`**: This generates Google Identity tokens, not signed JWTs
- ** Missing Swagger fields**: Missing `host`, `protocol`, or `path_translation` can break authentication
- ** Incorrect security type**: Using `apiKey` instead of `oauth2` in `securityDefinitions`
- ** Expired JWT timestamps**: JWT tokens must have current `iat` and `exp` values

### Testing Strategy

1. **Always test both scenarios**:
   - With valid JWT token (should return 200 OK)
   - Without token (should return 401 Unauthorized)

2. **Verify JWT generation**:
   - Check that `gcloud iam service-accounts sign-jwt` succeeds
   - Ensure the output file contains the signed JWT

3. **Monitor API Gateway logs** for authentication errors and debugging information


### API Gateway Compatibility
The Swagger2 specification is now compatible with Google Cloud API Gateway, enabling:
- **API Gateway deployment** with proper authentication
- **Swagger2 format** (OpenAPI v2) instead of v3
- **Google Cloud extensions** support


### Environment Variables Reference

The CI/CD pipeline configures the following environment variables. These are documented here for reference:

**Required environment variables:**
- `SIC_VECTOR_STORE`: URL of the SIC classification vector store service
- `FIRESTORE_DB_ID`: Firestore Database ID (required for result and feedback endpoints)

**Optional environment variables:**
- `GCP_PROJECT_ID`: Google Cloud Project ID (uses default project if not set)
- `SIC_LOOKUP_DATA_PATH`: Path to custom SIC lookup data file (defaults to package example data)
- `SIC_REPHRASE_DATA_PATH`: Path to custom SIC rephrase data file (defaults to package example data)