# Survey Assist API Guide

## Overview

The Survey Assist API is a FastAPI-based service that provides endpoints for industrial classification and data storage. This guide provides detailed information about the API's features, setup, and usage.

## Architecture

The API is built using:
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **SIC Classification Library**: Core classification functionality

## API Endpoints

### Configuration Endpoint
- **Path**: `/v1/survey-assist/config`
- **Method**: GET
- **Description**: Returns the current configuration settings including:
  - LLM model configuration
  - Data store settings
  - Classification prompts
  - Version-specific settings

### SIC Lookup Endpoint
- **Path**: `/v1/survey-assist/sic-lookup`
- **Method**: GET
- **Parameters**:
  - `description` (required): The business description to classify
  - `similarity` (optional): Boolean flag for similarity search
- **Description**: Performs SIC code lookup with two modes:
  - Exact match (similarity=false)
  - Similarity search (similarity=true)

## Integration with SIC Classification Library

The API integrates with the SIC Classification Library to provide:
- Standard Industrial Classification (SIC) code lookup
- Similarity-based classification
- Metadata for classifications
- Code division information

## Documentation

### Interactive Documentation
The API provides two types of interactive documentation:
1. **Swagger UI** (`/docs`)
   - Interactive API testing
   - Request/response schemas
   - Example values
   - Try-it-out functionality

2. **ReDoc** (`/redoc`)
   - Alternative documentation view
   - Clean, readable format
   - Schema visualisation

### API Specification
The OpenAPI specification is available at `/openapi.json`

## Development

### Prerequisites
- Python 3.12
- Poetry for dependency management
- Access to the SIC Classification Library

### Setup
1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run the API:
   ```bash
   make run-api
   ```

3. View documentation:
   ```bash
   make run-docs
   ```

### Testing
- API tests: `make api-tests`
- Unit tests: `make unit-tests`
- All tests: `make all-tests`

## Configuration

## Configuration

The API provides a configuration system that currently allows viewing the active configuration.

- The `/config` endpoint provides a read-only view of the current API configuration.
- Currently, the LLM configuration is static and cannot be modified via the API.

Configuration is managed through the `/config` endpoint and reflects the settings currently in use.

## Error Handling

The API provides clear error responses for:
- Missing required parameters
- Invalid input
- Internal server errors

All errors follow a consistent format with appropriate HTTP status codes.

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
