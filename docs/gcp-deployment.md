# Survey Assist API - GCP Deployment Guide

This document provides instructions for deploying the Survey Assist API to Google Cloud Platform (GCP) Cloud Run.

## Prerequisites

- Google Cloud SDK installed and configured
- Docker installed and running (colima for local development)
- Access to the target GCP project (survey-assist-sandbox, ons-survey-assist-dev, etc.)
- Appropriate IAM permissions for Cloud Run and Artifact Registry

## Local Testing with Containers

### 0. Set up GCP Authentication

Before running the containers locally, you need to authenticate with GCP:

```bash
# Authenticate with GCP
gcloud auth login

# Set your project
gcloud config set project ai-assist-tlfs-poc  # or your target project

# Verify authentication
gcloud auth list
```

**Note**: The containers need access to GCP services (Vertex AI). Your local GCP credentials are mounted into the container using the `-v ~/.config/gcloud:/home/appuser/.config/gcloud:ro` flag in the docker run command.

### 1. Build Docker Images

```bash
# Build survey-assist-api image
cd /path/to/survey-assist-api
docker build -t survey-assist-api:latest .

# Build SIC vector store image
cd /path/to/sic-classification-vector-store
docker build -t sic-vector-store:latest .
```

### 2. Run Containers Locally

```bash
# Create Docker network for container communication
docker network create survey-assist-network

# Run SIC vector store (takes ~5 minutes to start)
docker run -d --name sic-vector-store \
  --network survey-assist-network \
  -p 8088:8088 \
  sic-vector-store:latest

# Wait for SIC vector store to be ready
curl http://localhost:8088/v1/sic-vector-store/status

# Run survey-assist-api with credential mounting
docker run -d --name survey-assist-test -p 8080:8080 -e GOOGLE_CLOUD_PROJECT=ai-assist-tlfs-poc -v ~/.config/gcloud:/home/appuser/.config/gcloud:ro survey-assist-api:latest
```

### 3. Test Endpoints

```bash
# Test root endpoint
curl http://localhost:8080/

# Test config endpoint
curl http://localhost:8080/v1/survey-assist/config

# Test embeddings endpoint
curl http://localhost:8080/v1/survey-assist/embeddings

# Test SIC lookup endpoint
curl http://localhost:8080/v1/survey-assist/sic-lookup

# Test classify endpoint (POST)
curl -X POST http://localhost:8080/v1/survey-assist/classify \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Test result endpoint
curl http://localhost:8080/v1/survey-assist/result?result_id=test

**Note**: Some endpoints (sic-lookup, classify) may return errors in the local containerised environment because they expect a separate `sic-classification-library` service. These endpoints will work correctly in the production Cloud Run environment where all services are deployed separately.
```

## GCP Deployment

### 1. Configure GCP Project

```bash
# Set the target project
gcloud config set project survey-assist-sandbox  # or appropriate environment

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Build and Push Images

```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker europe-west2-docker.pkg.dev

# Build the survey-assist-api image
cd /path/to/survey-assist-api
docker build -t survey-assist-api:latest .

# Tag image for Artifact Registry
docker tag survey-assist-api:latest europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest

# Push image to Artifact Registry
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest
```

### 3. Deploy to Cloud Run

**Important**: The Cloud Run service must be configured to match the container port. Our container runs on port 8080, so the Cloud Run service must be configured accordingly.

#### Update Existing Cloud Run Service

If a Cloud Run service already exists, update it with the correct configuration:

```bash
# Update the service with correct port and resource configuration
gcloud run services update survey-assist-api \
  --port=8080 \
  --concurrency=160 \
  --timeout=60 \
  --cpu=1 \
  --memory=4Gi \
  --set-env-vars="BUCKET_NAME=survey-assist-sandbox-cloud-run-services,DATA_STORE=gcp" \
  --region=europe-west2 \
  --project=survey-assist-sandbox
```

**Key Configuration Details:**
- **Port**: 8080 (must match container port)
- **Concurrency**: 160 (matches successful UI service configuration)
- **Timeout**: 60s (reduced from 720s for better performance)
- **CPU**: 1 (reduced from 4 for cost optimisation)
- **Memory**: 4Gi (reduced from 8Gi for cost optimisation)
- **Environment Variables**: BUCKET_NAME and DATA_STORE set

#### Deploy New Cloud Run Service

If deploying a new service:

```bash
gcloud run deploy survey-assist-api \
  --image europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-api/survey-assist-api:latest \
  --platform managed \
  --region europe-west2 \
  --port 8080 \
  --memory 4Gi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 160 \
  --set-env-vars="BUCKET_NAME=survey-assist-sandbox-cloud-run-services,DATA_STORE=gcp" \
  --service-account api-cloud-run@survey-assist-sandbox.iam.gserviceaccount.com
```

### 4. Verify Deployment

```bash
# Check service status
gcloud run services describe survey-assist-api --region=europe-west2 --project=survey-assist-sandbox

# View logs
gcloud run services logs read survey-assist-api --region=europe-west2 --project=survey-assist-sandbox --limit=50
```

### 5. Test Deployed Endpoints

```bash
# Get the service URL
SURVEY_ASSIST_URL="https://survey-assist-api-670504361336.europe-west2.run.app"

# Test endpoints
curl $SURVEY_ASSIST_URL/
curl $SURVEY_ASSIST_URL/v1/survey-assist/config
curl $SURVEY_ASSIST_URL/v1/survey-assist/embeddings
curl $SURVEY_ASSIST_URL/v1/survey-assist/sic-lookup
curl -X POST $SURVEY_ASSIST_URL/v1/survey-assist/classify -H "Content-Type: application/json" -d '{"test": "data"}'
curl $SURVEY_ASSIST_URL/v1/survey-assist/result?result_id=test
```

## Troubleshooting

### Port Configuration Issues

**Problem**: Container fails to become healthy with "Startup probes timed out" error.

**Root Cause**: Mismatch between container port and Cloud Run service port configuration.

**Solution**: Ensure Cloud Run service is configured to use port 8080 (matching the container):

```bash
# Check current port configuration
gcloud run services describe survey-assist-api --region=europe-west2 --project=survey-assist-sandbox --format="value(spec.template.spec.containers[0].ports[0].containerPort)"

# Update port if needed
gcloud run services update survey-assist-api --port=8080 --region=europe-west2 --project=survey-assist-sandbox
```

### Resource Configuration

**Problem**: Service uses excessive resources (8Gi memory, 4 CPU).

**Solution**: Use optimised configuration matching successful UI service:

```bash
gcloud run services update survey-assist-api \
  --cpu=1 \
  --memory=4Gi \
  --concurrency=160 \
  --timeout=60 \
  --region=europe-west2 \
  --project=survey-assist-sandbox
```

### Common Issues

1. **Container fails to start due to GCP authentication**
   - Ensure service account has appropriate permissions
   - Check that GOOGLE_CLOUD_PROJECT environment variable is set

2. **SIC vector store connection fails**
   - Verify SIC_VECTOR_STORE environment variable is set correctly
   - Check that SIC vector store service is running and accessible

3. **Memory/CPU limits exceeded**
   - Increase memory and CPU allocation in Cloud Run deployment
   - Monitor resource usage in Cloud Console

4. **Timeout issues**
   - Increase timeout values for long-running operations
   - Consider implementing async processing for heavy workloads

### Monitoring and Logging

```bash
# View logs for survey-assist-api
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=survey-assist-api" --limit=50

# View logs for sic-vector-store
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sic-vector-store" --limit=50
```
