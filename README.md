# Survey Assist API

A FastAPI-based service for classifying job titles and descriptions using SIC (Standard Industrial Classification) and SOC (Standard Occupational Classification) codes.

## Features

- **SIC Classification**: Classify business activities using SIC codes
- **SOC Classification**: Classify job roles using SOC codes  
- **Combined Classification**: Perform both SIC and SOC classifications in a single request
- **Generic Response Format**: Unified response structure for all classification types

## API Endpoints

### Classify Endpoint

`POST /v1/survey-assist/classify`

Classifies job titles and descriptions using the specified classification type.

#### Request Format

```json
{
  "llm": "gemini",
  "type": "sic|soc|sic_soc",
  "job_title": "Software Engineer",
  "job_description": "Developing web applications and software solutions",
  "org_description": "Technology company"
}
```

#### Response Format

The API now returns a generic response format that supports multiple classification types:

```json
{
  "requested_type": "sic|soc|sic_soc",
  "results": [
    {
      "type": "sic|soc",
      "classified": true|false,
      "followup": "Additional question if needed",
      "code": "Classification code",
      "description": "Classification description", 
      "candidates": [
        {
          "code": "Candidate code",
          "descriptive": "Candidate description",
          "likelihood": 0.8
        }
      ],
      "reasoning": "Explanation of the classification"
    }
  ]
}
```

#### Classification Types

- **`sic`**: Standard Industrial Classification - classifies business activities
- **`soc`**: Standard Occupational Classification - classifies job roles
- **`sic_soc`**: Combined classification - returns both SIC and SOC results

#### Examples

**SIC Classification:**
```bash
curl -X POST http://localhost:8080/v1/survey-assist/classify \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Electrician",
    "job_description": "Installing and maintaining electrical systems in buildings",
    "org_description": "Electrical contracting company"
  }'
```

**Response:**
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
          "likelihood": 0.9
        }
      ],
      "reasoning": "The respondent's data indicates an electrical contracting company with a job title of 'Electrician' and job description involving 'Installing and maintaining electrical systems in buildings'. This directly aligns with SIC code 43210: Electrical installation, which covers electrical installation work in buildings and construction projects."
    }
  ]
}
```

**SOC Classification:**
```bash
curl -X POST http://localhost:8080/v1/survey-assist/classify \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini", 
    "type": "soc",
    "job_title": "Electrician",
    "job_description": "Installing and maintaining electrical systems in buildings",
    "org_description": "Electrical contracting company"
  }'
```

**Response:**
```json
{
  "requested_type": "soc",
  "results": [
    {
      "type": "soc",
      "classified": true,
      "followup": null,
      "code": "5241",
      "description": "Electricians and electrical fitters",
      "candidates": [
        {
          "code": "5241",
          "descriptive": "Electricians and electrical fitters",
          "likelihood": 0.9
        }
      ],
      "reasoning": "The job title 'Electrician' and job description mentioning 'Installing and maintaining electrical systems in buildings' directly corresponds to SOC code 5241: Electricians and electrical fitters. This code specifically covers electrical installation and maintenance work in buildings and construction projects."
    }
  ]
}
```

**Combined SIC and SOC Classification:**
```bash
curl -X POST http://localhost:8080/v1/survey-assist/classify \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic_soc", 
    "job_title": "Electrician",
    "job_description": "Installing and maintaining electrical systems in buildings",
    "org_description": "Electrical contracting company"
  }'
```

**Response:**
```json
{
  "requested_type": "sic_soc",
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
          "likelihood": 0.9
        }
      ],
      "reasoning": "The respondent's data indicates an electrical contracting company with a job title of 'Electrician' and job description involving 'Installing and maintaining electrical systems in buildings'. This directly aligns with SIC code 43210: Electrical installation, which covers electrical installation work in buildings and construction projects."
    },
    {
      "type": "soc",
      "classified": true,
      "followup": null,
      "code": "5241",
      "description": "Electricians and electrical fitters",
      "candidates": [
        {
          "code": "5241",
          "descriptive": "Electricians and electrical fitters",
          "likelihood": 0.9
        }
      ],
      "reasoning": "The job title 'Electrician' and job description mentioning 'Installing and maintaining electrical systems in buildings' directly corresponds to SOC code 5241: Electricians and electrical fitters. This code specifically covers electrical installation and maintenance work in buildings and construction projects."
    }
  ]
}
```

## Development

### Prerequisites

- Python 3.12+
- Poetry for dependency management

### Installation

```bash
poetry install
```

### Running the API

```bash
make run-api
```

The API will be available at `http://localhost:8080`

### Running Tests

```bash
poetry run pytest
```

## Architecture

The API uses a modular architecture with:

- **Vector Store Clients**: For SIC and SOC vector store interactions
- **LLM Services**: For classification using AI models
- **Rephrase Client**: For improving SIC descriptions
- **Generic Response Models**: Unified structure for all classification types

## Recent Changes

### Generic Response Format (Latest)

The classification endpoint now returns a generic response format that:

- Returns an array of results instead of a single object
- Includes a `type` field in each result to identify the classification type
- Uses unified field names (`code`, `description`, `candidates`) instead of type-specific ones
- Supports combined SIC and SOC classifications in a single request
- Maintains backward compatibility through legacy models

This change makes the API more flexible and easier to extend for future classification types.
