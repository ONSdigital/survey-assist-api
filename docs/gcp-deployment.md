# Survey Assist API - GCP Deployment Guide

This document provides the essential steps for deploying the Survey Assist API to Google Cloud Platform (GCP) Cloud Run.

## Prerequisites

- Google Cloud SDK installed and configured
- Docker installed and running (colima for local development)
- Access to the target GCP project ({PROJECT_ID})

## Deployment Process

### 1. Build Docker Image

```bash
# Build the survey-assist-api image
cd /path/to/survey-assist-api
docker build -t survey-assist-api:latest .
```

### 2. Push to Artifact Registry

```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker europe-west2-docker.pkg.dev

# Tag image for Artifact Registry
docker tag survey-assist-api:latest europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest

# Push image to Artifact Registry
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest
```

### 3. Deploy to Cloud Run

```bash
# Update existing service with new image
gcloud run services update survey-assist-api \
  --image=europe-west2-docker.pkg.dev/{PROJECT_ID}/survey-assist-api/survey-assist-api:latest \
  --port=8080 \
  --concurrency=160 \
  --timeout=60s \
  --cpu=1 \
  --memory=4Gi \
  --set-env-vars="GCP_BUCKET_NAME={BUCKET_NAME},DATA_STORE=gcp" \
  --region={REGION} \
  --project={PROJECT_ID}
```

### 4. Configure Service Account and Permissions

```bash
# Set the service account for the Cloud Run service
gcloud run services update survey-assist-api \
  --service-account={SURVEY_ASSIST_SERVICE_ACCOUNT} \
  --region={REGION} \
  --project={PROJECT_ID}

# Grant necessary IAM roles
gcloud projects add-iam-policy-binding {PROJECT_ID} \
  --member="serviceAccount:{SURVEY_ASSIST_SERVICE_ACCOUNT}" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding {PROJECT_ID} \
  --member="serviceAccount:{SURVEY_ASSIST_SERVICE_ACCOUNT}" \
  --role="roles/iam.serviceAccountTokenCreator"

# Ensure service requires authentication (remove public access if needed)
gcloud run services remove-iam-policy-binding survey-assist-api \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region={REGION} \
  --project={PROJECT_ID}

# Redeploy to apply authentication changes
gcloud run services update survey-assist-api \
  --image=europe-west2-docker.pkg.dev/{PROJECT_ID}/survey-assist-api/survey-assist-api:latest \
  --region={REGION} \
  --project={PROJECT_ID}
```

### 5. Test Direct Cloud Run Endpoints

```bash
# Test endpoints with authentication
SURVEY_ASSIST_URL="$(gcloud run services describe survey-assist-api --region={REGION} --project={PROJECT_ID} --format='value(status.url)')"

curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SURVEY_ASSIST_URL/
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SURVEY_ASSIST_URL/v1/survey-assist/config
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SURVEY_ASSIST_URL/v1/survey-assist/sic-lookup
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" -H "Content-Type: application/json" -d '{"llm": "gemini", "type": "sic", "job_title": "Test", "job_description": "Test", "org_description": "Test organisation"}' "$SURVEY_ASSIST_URL/v1/survey-assist/classify"
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

Set the `SIC_VECTOR_STORE` environment variable to enable secure communication with the vector store service:

```bash
# Set environment variable for service-to-service communication
gcloud run services update survey-assist-api \
  --set-env-vars="SIC_VECTOR_STORE={VECTOR_STORE_SERVICE_URL}" \
  --region=europe-west2 \
  --project={PROJECT_ID}
```

### Service Account Permissions

The `survey-assist-api` service account requires the following IAM roles for service-to-service communication:

```bash
# Grant Cloud Run Invoker role to the calling service
gcloud run services add-iam-policy-binding {VECTOR_STORE_SERVICE_NAME} \
  --member="serviceAccount:{SURVEY_ASSIST_SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region={REGION} \
  --project={PROJECT_ID}

# Grant IAM Service Account Token Creator role (if needed for token generation)
gcloud projects add-iam-policy-binding {PROJECT_ID} \
  --member="serviceAccount:{SURVEY_ASSIST_SERVICE_ACCOUNT}" \
  --role="roles/iam.serviceAccountTokenCreator"
```

### Testing Service-to-Service Communication

Test the complete end-to-end flow including service-to-service authentication:

```bash
# Test with complete request including org_description
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
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

## API Gateway Setup

### 6. Fix Swagger2 Compatibility Issues

The original spec contains OpenAPI 3.0 features that aren't supported by API Gateway. Fix these issues:

```bash
# Remove examples fields (not supported in Swagger 2.0)
jq 'del(.. | select(type == "object" and has("examples")).examples)' swagger2_original.json > swagger2_fixed.json

# Remove anyOf fields (not supported in Swagger 2.0)
jq 'del(.. | select(type == "object" and has("anyOf")).anyOf)' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json

# Add missing type field for data_path parameter
jq '(.paths."/v1/survey-assist/sic-lookup".get.parameters[] | select(.name == "data_path")) += {"type": "string"}' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json

# Add Google Cloud API Gateway extensions for JWT authentication
jq '. + {"x-google-backend": {"address": "{SURVEY_ASSIST_API_URL}", "protocol": "h2", "path_translation": "APPEND_PATH_TO_ADDRESS"}, "host": "{API_GATEWAY_HOSTNAME}", "securityDefinitions": {"backend_api_access": {"authorizationUrl": "", "flow": "implicit", "type": "oauth2", "x-google-issuer": "{SERVICE_ACCOUNT_EMAIL}", "x-google-jwks_uri": "https://www.googleapis.com/robot/v1/metadata/x509/{SERVICE_ACCOUNT_EMAIL}", "x-google-audiences": "{API_GATEWAY_HOSTNAME}"}}, "security": [{"backend_api_access": []}]}' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json

# Note: Replace placeholders with actual values:
# {SURVEY_ASSIST_API_URL}: Your Cloud Run service URL
# {API_GATEWAY_HOSTNAME}: Your API Gateway hostname
# {SERVICE_ACCOUNT_EMAIL}: Service account that will sign JWTs
```

### 7. Deploy the Fixed Specification

```bash
# Create new API config with fixed spec
gcloud api-gateway api-configs create survey-assist-api-config-v3 \
  --api=survey-assist-api \
  --openapi-spec=swagger2_fixed.json \
  --project={PROJECT_ID} \
  --backend-auth-service-account={BACKEND_AUTH_SERVICE_ACCOUNT}
```

### 8. Update the Gateway

```bash
# Update existing gateway to use new config
gcloud api-gateway gateways update survey-assist-api-gw \
  --api-config=survey-assist-api-config-v3 \
  --api=survey-assist-api \
  --location={REGION} \
  --project={PROJECT_ID}
```

### 9. Test API Gateway Endpoints

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

# Test SIC lookup endpoint
curl --header "Authorization: Bearer ${JWT_TOKEN}" \
  "https://$GATEWAY_URL/v1/survey-assist/sic-lookup?description=electrical%20installation"

# Test classify endpoint
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

# Test result endpoint
curl -X POST --header "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"survey_id":"test-123","case_id":"test-456","user":"test.user","time_start":"2024-01-01T10:00:00Z","time_end":"2024-01-01T10:05:00Z","responses":[]}' \
  "https://$GATEWAY_URL/v1/survey-assist/result"

# Test authentication enforcement (should return 401)
curl "https://$GATEWAY_URL/v1/survey-assist/config"
```

**Expected Responses**:
- **Config**: Returns LLM model, embedding model, and prompt configurations
- **Embeddings**: Returns vector store status and metadata
- **SIC Lookup**: Returns SIC code lookup results
- **Classify**: Returns SIC/SOC classification with follow-up questions
  - **Rephrasing enabled**: `candidates[].descriptive` shows user-friendly descriptions (e.g., "Crop growing", "Dairy farming")
  - **Rephrasing disabled**: `candidates[].descriptive` shows original SIC descriptions
  - **Main description**: Always shows official SIC code description
- **Result**: Returns confirmation of stored survey results
- **Unauthenticated**: Returns `{"code":401,"message":"Jwt is missing"}`
**API Gateway Endpoints:**
All endpoints are accessible via the API Gateway at `{API_GATEWAY_URL}/v1/survey-assist/`:

- **Config**: `config` - Get API configuration and prompt settings
- **Embeddings**: `embeddings` - Get vector store status and metadata
- **SIC Lookup**: `sic-lookup` - Lookup SIC codes by description
- **Classification**: `classify` - Classify job descriptions to SIC/SOC codes
- **Results**: `result` - Store survey interaction results

## API Gateway Authentication with JWT Tokens

### Important: JWT vs Google Identity Tokens

**API Gateway requires signed JWT tokens, NOT Google Identity tokens.** This is a critical distinction:

- **❌ Google Identity Token** (`gcloud auth print-identity-token`): This is a Google-generated token that identifies the user but cannot be used for API Gateway authentication
- **✅ Signed JWT Token**: This is a custom JWT token that must be signed by the service account specified in the Swagger spec's `x-google-issuer` field

### JWT Token Generation Process

To authenticate with API Gateway, you must generate a signed JWT token:

#### 1. Create JWT Payload

Create a `payload.json` file with the required claims:

```json
{
  "iat": <current_timestamp>,
  "exp": <current_timestamp + 3600>,
  "iss": "<service-account-email>",
  "aud": "<api-gateway-hostname>",
  "sub": "<service-account-email>",
  "email": "<service-account-email>"
}
```

**Required fields:**
- `iat`: Issued at timestamp (current time)
- `exp`: Expiration timestamp (current time + 1 hour)
- `iss`: Issuer (must match `x-google-issuer` in Swagger spec)
- `aud`: Audience (must match `x-google-audiences` in Swagger spec)
- `sub`: Subject (service account email)
- `email`: Service account email

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

## Updating Existing Images

### Quick Update (Recommended)
To update an existing image with new code changes:

```bash
# 1. Build with same tag (overwrites existing image)
docker build -t europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest .

# 2. Push to update registry
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest

# 3. Deploy updated image to Cloud Run
gcloud run services update survey-assist-api \
  --image=europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest \
  --port=8080 \
  --concurrency=160 \
  --timeout=60s \
  --cpu=1 \
  --memory=4Gi \
  --set-env-vars="GCP_BUCKET_NAME=survey-assist-sandbox-cloud-run-services,DATA_STORE=gcp" \
  --region=europe-west2 \
  --project=survey-assist-sandbox
```

### Alternative: Versioned Updates
For better tracking, use versioned tags:

```bash
# 1. Build with version tag
docker build -t europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:v1.4 .

# 2. Push versioned image
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:v1.4

# 3. Deploy specific version
gcloud run services update survey-assist-api \
  --image=europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:v1.4 \
  --region=europe-west2 \
  --project=survey-assist-sandbox
```

### Clean Update (Remove Old Images)
If you want to clean up old images:

```bash
# 1. Remove old local images
docker rmi survey-assist-api:latest
docker rmi europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest

# 2. Build fresh with same tag
docker build -t europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest .

# 3. Push and deploy (same as Quick Update)
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest
gcloud run services update survey-assist-api --image=... # (same command as above)
```

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
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$(gcloud run services describe survey-assist-api --region=europe-west2 --project=survey-assist-sandbox --format='value(status.url)')/swagger2.json"

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

- **❌ Using `gcloud auth print-identity-token`**: This generates Google Identity tokens, not signed JWTs
- **❌ Missing Swagger fields**: Missing `host`, `protocol`, or `path_translation` can break authentication
- **❌ Incorrect security type**: Using `apiKey` instead of `oauth2` in `securityDefinitions`
- **❌ Expired JWT timestamps**: JWT tokens must have current `iat` and `exp` values

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


### Environment Variables
Ensure correct environment variable name is used:
```bash
gcloud run services update survey-assist-api --set-env-vars="GCP_BUCKET_NAME=survey-assist-sandbox-cloud-run-services,DATA_STORE=gcp" --region=europe-west2
```