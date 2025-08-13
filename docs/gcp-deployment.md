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

# Add Google Cloud API Gateway extensions
jq '. + {"x-google-backend": {"address": "{SURVEY_ASSIST_API_URL}"}, "x-google-issuer": "https://accounts.google.com", "x-google-jwks_uri": "https://www.googleapis.com/oauth2/v1/certs", "x-google-audiences": "{PROJECT_ID}", "securityDefinitions": {"google_id_token": {"type": "apiKey", "name": "Authorization", "in": "header", "description": "Google ID token for authentication"}}}' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json

# Add security to all endpoints
jq '(.paths[][] | select(type == "object" and has("tags"))) += {"security": [{"google_id_token": []}]}' swagger2_fixed.json > temp.json && mv temp.json swagger2_fixed.json
```

### 7. Deploy the Fixed Specification

```bash
# Create new API config with fixed spec
gcloud api-gateway api-configs create survey-assist-api-config-v3 \
  --api=survey-assist-api \
  --openapi-spec=swagger2_fixed.json \
  --project={PROJECT_ID}
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

```bash
# Get the current gateway URL
GATEWAY_URL="$(gcloud api-gateway gateways describe survey-assist-api-gw --location={REGION} --project={PROJECT_ID} --format='value(defaultHostname)')"

# Test config endpoint
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://$GATEWAY_URL/v1/survey-assist/config"

# Test SIC lookup endpoint
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://$GATEWAY_URL/v1/survey-assist/sic-lookup?description=electrical%20installation"

# Test classify endpoint
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"llm":"gemini","type":"sic","job_title":"Software Engineer","job_description":"I develop web applications"}' \
  "https://$GATEWAY_URL/v1/survey-assist/classify"

# Test result endpoint
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"survey_id":"test-123","case_id":"test-456","user":"test.user","time_start":"2024-01-01T10:00:00Z","time_end":"2024-01-01T10:05:00Z","responses":[]}' \
  "https://$GATEWAY_URL/v1/survey-assist/result"
```
**API Gateway Endpoints:**
All endpoints are accessible via the API Gateway at `{API_GATEWAY_URL}/v1/survey-assist/`:

- **Config**: `config`
- **SIC Lookup**: `sic-lookup`
- **Classification**: `classify`
- **Results**: `result`

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

# Verify old endpoints are removed
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$(gcloud run services describe survey-assist-api --region=europe-west2 --project=survey-assist-sandbox --format='value(status.url)')/docs"
# Should return 404
```

### API Gateway Compatibility
The Swagger2 specification is now compatible with Google Cloud API Gateway, enabling:
- **API Gateway deployment** with proper authentication
- **Swagger2 format** (OpenAPI v2) instead of v3
- **Google Cloud extensions** support

## Troubleshooting

### Port Configuration
If container fails to start, ensure Cloud Run service uses port 8080:
```bash
# Get authentication token
gcloud auth print-identity-token

# Use in requests
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://{GATEWAY_URL}/v1/survey-assist/config"
```

### Environment Variables
Ensure correct environment variable name is used:
```bash
gcloud run services update survey-assist-api --set-env-vars="GCP_BUCKET_NAME=survey-assist-sandbox-cloud-run-services,DATA_STORE=gcp" --region=europe-west2
```