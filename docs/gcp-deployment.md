# Survey Assist API - GCP Deployment Guide

This document provides the essential steps for deploying the Survey Assist API to Google Cloud Platform (GCP) Cloud Run.

## Prerequisites

- Google Cloud SDK installed and configured
- Docker installed and running (colima for local development)
- Access to the target GCP project (survey-assist-sandbox)

## Deployment Steps

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

### 4. Test Deployment

```bash
# Test endpoints with authentication
SURVEY_ASSIST_URL="https://survey-assist-api-670504361336.europe-west2.run.app"

curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SURVEY_ASSIST_URL/
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SURVEY_ASSIST_URL/v1/survey-assist/config
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SURVEY_ASSIST_URL/v1/survey-assist/sic-lookup
curl -X POST -H "Authorization: Bearer $(gcloud auth print-identity-token)" -H "Content-Type: application/json" -d '{"llm": "gemini", "type": "sic", "job_title": "Test", "job_description": "Test"}' "$SURVEY_ASSIST_URL/v1/survey-assist/classify"
```

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

## Current Status

**All endpoints working**: root, config, classify, sic-lookup, result  
**Service URL**: https://survey-assist-api-670504361336.europe-west2.run.app  
**Environment**: survey-assist-sandbox

## Recent Updates

### Swagger2 Support (August 2025)
The API has been updated to support Swagger2 (OpenAPI v2) for Google Cloud API Gateway compatibility:

#### Changes Made
- **Added `fastapi_swagger2` dependency** (v0.2.4)
- **Replaced OpenAPI v3 endpoints** with Swagger2 endpoints
- **Updated documentation URLs** from `/docs` to `/swagger2/docs`

#### New Endpoints
- `/swagger2.json` - Swagger2 specification (API Gateway compatible)
- `/swagger2/docs` - Swagger2 UI
- `/swagger2/redoc` - ReDoc for Swagger2

#### Breaking Changes
- `/docs`, `/redoc`, `/openapi.json` endpoints removed
- **Documentation URLs updated** - all references changed to `/swagger2/*`

#### Testing Swagger2
```bash
# Test new Swagger2 endpoints
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://survey-assist-api-670504361336.europe-west2.run.app/swagger2.json"

# Verify old endpoints are removed
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://survey-assist-api-670504361336.europe-west2.run.app/docs"
# Should return 404
```

#### API Gateway Compatibility
The Swagger2 specification is now compatible with Google Cloud API Gateway, enabling:
- **API Gateway deployment** with proper authentication
- **Swagger2 format** (OpenAPI v2) instead of v3
- **Google Cloud extensions** support

## Troubleshooting

### Port Configuration
If container fails to start, ensure Cloud Run service uses port 8080:
```bash
gcloud run services update survey-assist-api --port=8080 --region=europe-west2
```

### Environment Variables
Ensure correct environment variable name is used:
```bash
gcloud run services update survey-assist-api --set-env-vars="GCP_BUCKET_NAME=survey-assist-sandbox-cloud-run-services,DATA_STORE=gcp" --region=europe-west2
```
