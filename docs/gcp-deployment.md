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

### 2. Create Artifact Registry Repository

```bash
# Create repository for Docker images
gcloud artifacts repositories create survey-assist-repo \
  --repository-format=docker \
  --location=europe-west2 \
  --description="Survey Assist API Docker images"
```

### 3. Build and Push Images

```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker europe-west2-docker.pkg.dev

# Tag images for Artifact Registry
docker tag survey-assist-api:latest europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-repo/survey-assist-api:latest
docker tag sic-vector-store:latest europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-repo/sic-vector-store:latest

# Push images
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-repo/survey-assist-api:latest
docker push europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-repo/sic-vector-store:latest
```

### 4. Deploy to Cloud Run

#### Deploy SIC Vector Store

```bash
gcloud run deploy sic-vector-store \
  --image europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-repo/sic-vector-store:latest \
  --platform managed \
  --region europe-west2 \
  --allow-unauthenticated \
  --port 8088 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars="VECTOR_STORE_DIR=/app/sic_classification_vector_store/data/vector_store"
```

#### Deploy Survey Assist API

```bash
gcloud run deploy survey-assist-api \
  --image europe-west2-docker.pkg.dev/survey-assist-sandbox/survey-assist-repo/survey-assist-api:latest \
  --platform managed \
  --region europe-west2 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=survey-assist-sandbox,SIC_VECTOR_STORE=https://sic-vector-store-url"
```

**Note**: Replace `sic-vector-store-url` with the actual URL of the deployed SIC vector store service.

### 5. Configure API Gateway

The API Gateway should be configured to route traffic to the survey-assist-api Cloud Run service. The latest OpenAPI schema should be deployed to API Gateway.

### 6. Test Deployed Endpoints

```bash
# Get the service URLs
SURVEY_ASSIST_URL=$(gcloud run services describe survey-assist-api --region=europe-west2 --format="value(status.url)")
SIC_VECTOR_STORE_URL=$(gcloud run services describe sic-vector-store --region=europe-west2 --format="value(status.url)")

# Test endpoints
curl $SURVEY_ASSIST_URL/
curl $SURVEY_ASSIST_URL/v1/survey-assist/config
curl $SURVEY_ASSIST_URL/v1/survey-assist/embeddings
curl $SURVEY_ASSIST_URL/v1/survey-assist/sic-lookup
curl -X POST $SURVEY_ASSIST_URL/v1/survey-assist/classify -H "Content-Type: application/json" -d '{"test": "data"}'
curl $SURVEY_ASSIST_URL/v1/survey-assist/result?result_id=test
```

## Environment-Specific Configuration

### Sandbox Environment
- Project: `survey-assist-sandbox`
- Region: `europe-west2`
- Service URLs: Available via Cloud Run console

### Development Environment
- Project: `ons-survey-assist-dev`
- Region: `europe-west2`
- Service URLs: Available via Cloud Run console

### Pre-production Environment
- Project: `ons-survey-assist-preprod`
- Region: `europe-west2`
- Service URLs: Available via Cloud Run console

### Production Environment
- Project: `ons-survey-assist-prod`
- Region: `europe-west2`
- Service URLs: Available via Cloud Run console

## Troubleshooting



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

## Security Considerations

- Both containers run as non-root user (appuser)
- GCP credentials are mounted securely
- Network communication is isolated via Docker networks
- Cloud Run provides automatic HTTPS and authentication

## Performance Optimisation

- SIC vector store uses 4GB memory and 2 CPU cores for optimal performance
- Survey Assist API uses 2GB memory and 1 CPU core
- Consider implementing caching for frequently accessed data
- Monitor and adjust resource allocation based on usage patterns

## Next Steps

1. Set up CI/CD pipeline using Cloud Build
2. Implement automated testing in the deployment pipeline
3. Configure monitoring and alerting
4. Set up backup and disaster recovery procedures
5. Document API usage and integration guidelines 