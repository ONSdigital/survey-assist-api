# Survey Assist API

The Survey Assist API - Used to access backend data processing services such as classification

## Overview

The Survey Assist API implemented in Fast API

## Features

- Fast API with endpoints for lookup and classification of SIC (Standard Industrial Classifier)
- **Rephrasing Toggle**: Control SIC description rephrasing via API options for testing and development
- **Firestore Integration**: Store survey results and feedback data in Google Cloud Firestore
- **List Results Endpoint**: Query survey results
- Deployed in GCP using Terraform
- Uses the following cloud services:
  - Cloud Run
  - API Gateway
  - Firestore Database
  - JWT Authentication with backend API
  - CI/CD pipeline for automated deployment

## Prerequisites

Ensure you have the following installed on your local machine:

- [ ] Python 3.12 (Recommended: use `pyenv` to manage versions)
- [ ] `poetry` (for dependency management)
- [ ] Colima (if running locally with containers)
- [ ] Terraform (for infrastructure management)
- [ ] Google Cloud SDK (`gcloud`) with appropriate permissions

### Local Development Setup

The Makefile defines a set of commonly used commands and workflows.  Where possible use the files defined in the Makefile.

#### Clone the repository

```bash
git clone https://github.com/ONSdigital/survey-assist-api.git
cd survey-assist-api
```

#### Install Dependencies

```bash
poetry install
```

#### Run the Application Locally

To run the application locally execute:

```bash
make run-api
```

### GCP Setup

Placeholder

### Code Quality

Code quality and static analysis will be enforced using isort, black, ruff, mypy and pylint. Security checking will be enhanced by running bandit.

To check the code quality, but only report any errors without auto-fix run:

```bash
make check-python-nofix
```

To check the code quality and automatically fix errors where possible run:

```bash
make check-python
```

### Documentation

Documentation is available in the docs folder and can be viewed using mkdocs

```bash
make run-docs
```

### Testing

Pytest is used for testing alongside pytest-cov for coverage testing.  [/tests/conftest.py](/tests/conftest.py) defines config used by the tests.

API testing is added to the [/tests/tests_api.py](./tests/tests_api.py)

```bash
make api-tests
```

Unit testing for utility functions is added to the [/tests/tests_utils.py](./tests/tests_utils.py)

```bash
make unit-tests
```

All tests can be run using

```bash
make all-tests
```

The API supports the following environment variables:

- `GCP_PROJECT_ID`: Google Cloud Project ID
- `FIRESTORE_DB_ID`: Firestore Database ID
- `SIC_LOOKUP_DATA_PATH`: Path to SIC lookup data file
- `SIC_REPHRASE_DATA_PATH`: Path to SIC rephrase data file 
- `SIC_VECTOR_STORE`: URL of the vector store service
