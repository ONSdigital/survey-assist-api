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

## Current Status

✅ **All endpoints working**: root, config, classify, sic-lookup, result  
✅ **Service URL**: https://survey-assist-api-670504361336.europe-west2.run.app  
✅ **Environment**: survey-assist-sandbox

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
