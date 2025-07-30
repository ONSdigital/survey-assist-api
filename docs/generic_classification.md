# Generic Classification API

This document describes the generic classification functionality that supports both SIC (Standard Industrial Classification) and SOC (Standard Occupational Classification) in a unified API.

## Overview

The Survey Assist API supports generic classification responses that can handle both SIC and SOC classification types. This allows for more flexible and extensible classification capabilities while maintaining backward compatibility.

## Endpoints

### Generic Classification Endpoint

**POST** `/v1/survey-assist/classify`

This endpoint provides generic classification functionality that can handle SIC, SOC, or combined SIC+SOC classification.

### Result Storage Endpoints

**POST** `/v1/survey-assist/result`

Store survey results that can contain SIC and/or SOC classification data.

**GET** `/v1/survey-assist/result`

Retrieve survey results using a result ID.

#### Request Format

```json
{
  "llm": "gemini-1.5-flash",
  "type": "sic|soc|sic_soc",
  "job_title": "string",
  "job_description": "string",
  "org_description": "string (optional)"
}
```

#### Response Format

The response follows a generic structure that can accommodate multiple classification types:

```json
{
  "requested_type": "sic|soc|sic_soc",
  "results": [
    {
      "type": "sic|soc",
      "classified": true|false,
      "followup": "string|null",
      "code": "string|null",
      "description": "string|null",
      "candidates": [
        {
          "code": "string",
          "descriptive": "string",
          "likelihood": 0.0-1.0
        }
      ],
      "reasoning": "string"
    }
  ]
}
```

#### Classification Types

- **`sic`**: Perform SIC classification only
- **`soc`**: Perform SOC classification only  
- **`sic_soc`**: Perform both SIC and SOC classification

## Examples

### SIC Classification Only

**Request:**
```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini-1.5-flash",
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
      "classified": false,
      "followup": "Please specify if this is electrical or plumbing installation.",
      "code": null,
      "description": null,
      "candidates": [
        {
          "code": "43210",
          "descriptive": "Electrical installation",
          "likelihood": 0.8
        },
        {
          "code": "43220",
          "descriptive": "Plumbing, heat and air-conditioning installation",
          "likelihood": 0.2
        }
      ],
      "reasoning": "The respondent's data indicates electrical work but needs clarification on specific installation type..."
    }
  ]
}
```

### SOC Classification Only

**Request:**
```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini-1.5-flash",
    "type": "soc",
    "job_title": "Farm Worker",
    "job_description": "Growing crops and vegetables",
    "org_description": "Agricultural farm"
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
      "code": "9111",
      "description": "Farm workers",
      "candidates": [
        {
          "code": "9111",
          "descriptive": "Farm workers",
          "likelihood": 1.0
        }
      ],
      "reasoning": "The respondent's data clearly indicates farm work activities..."
    }
  ]
}
```

### Combined SIC and SOC Classification

**Request:**
```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini-1.5-flash",
    "type": "sic_soc",
    "job_title": "Farm Worker",
    "job_description": "Growing crops and vegetables",
    "org_description": "Agricultural farm"
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
      "code": "01110",
      "description": "Growing of cereals (except rice), legumes and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Growing of cereals (except rice), legumes and oil seeds",
          "likelihood": 0.9
        },
        {
          "code": "01130",
          "descriptive": "Growing of vegetables and melons, roots and tubers",
          "likelihood": 0.8
        }
      ],
      "reasoning": "The respondent's data indicates crop growing activities..."
    },
    {
      "type": "soc",
      "classified": true,
      "followup": null,
      "code": "9111",
      "description": "Farm workers",
      "candidates": [
        {
          "code": "9111",
          "descriptive": "Farm workers",
          "likelihood": 1.0
        }
      ],
      "reasoning": "The respondent's data clearly indicates farm work activities..."
    }
  ]
}
```

### Result Storage Examples

#### Store Survey Result

**POST** `/v1/survey-assist/result`

**Request:**
```bash
curl -X POST "http://localhost:8080/v1/survey-assist/result" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id": "test-survey-123",
    "case_id": "test-case-456",
    "user": "test.userSA187",
    "time_start": "2024-03-19T10:00:00Z",
    "time_end": "2024-03-19T10:05:00Z",
    "responses": [
      {
        "person_id": "person-001",
        "time_start": "2024-03-19T10:00:00Z",
        "time_end": "2024-03-19T10:02:00Z",
        "survey_assist_interactions": [
          {
            "type": "classify",
            "flavour": "sic_soc",
            "time_start": "2024-03-19T10:00:30Z",
            "time_end": "2024-03-19T10:01:30Z",
            "input": [
              {
                "field": "job_title",
                "value": "Electrician"
              },
              {
                "field": "job_description",
                "value": "Installing and maintaining electrical systems in buildings"
              },
              {
                "field": "org_description",
                "value": "Electrical contracting company"
              }
            ],
            "response": [
              {
                "type": "sic",
                "classified": false,
                "followup": "Please specify if this is electrical or plumbing installation.",
                "code": null,
                "description": null,
                "candidates": [
                  {
                    "code": "43210",
                    "descriptive": "Electrical installation",
                    "likelihood": 0.8
                  },
                  {
                    "code": "43220",
                    "descriptive": "Plumbing, heat and air-conditioning installation",
                    "likelihood": 0.2
                  }
                ],
                "reasoning": "The respondent'\''s data indicates electrical work but needs clarification on specific installation type..."
              },
              {
                "type": "soc",
                "classified": true,
                "followup": null,
                "code": "5245",
                "description": "Electricians and electrical fitters",
                "candidates": [
                  {
                    "code": "5245",
                    "descriptive": "Electricians and electrical fitters",
                    "likelihood": 0.95
                  }
                ],
                "reasoning": "The respondent'\''s data clearly indicates electrical work activities..."
              }
            ]
          }
        ]
      }
    ]
  }'
```

**Response:**
```json
{
  "message": "Result stored successfully",
  "result_id": "test-survey-123/test.userSA187/2024-03-19/10_01_30.json"
}
```

#### Retrieve Survey Result

**GET** `/v1/survey-assist/result?result_id=test-survey-123/test.userSA187/2024-03-19/10_01_30.json`

**Response:**
```json
{
  "survey_id": "test-survey-123",
  "case_id": "test-case-456",
  "user": "test.userSA187",
  "time_start": "2024-03-19T10:00:00Z",
  "time_end": "2024-03-19T10:05:00Z",
  "responses": [
    {
      "person_id": "person-001",
      "time_start": "2024-03-19T10:00:00Z",
      "time_end": "2024-03-19T10:02:00Z",
      "survey_assist_interactions": [
        {
          "type": "classify",
          "flavour": "sic_soc",
          "time_start": "2024-03-19T10:00:30Z",
          "time_end": "2024-03-19T10:01:30Z",
          "input": [
            {
              "field": "job_title",
              "value": "Electrician"
            },
            {
              "field": "job_description",
              "value": "Installing and maintaining electrical systems in buildings"
            },
            {
              "field": "org_description",
              "value": "Electrical contracting company"
            }
          ],
          "response": [
            {
              "type": "sic",
              "classified": false,
              "followup": "Please specify if this is electrical or plumbing installation.",
              "code": null,
              "description": null,
              "candidates": [
                {
                  "code": "43210",
                  "descriptive": "Electrical installation",
                  "likelihood": 0.8
                },
                {
                  "code": "43220",
                  "descriptive": "Plumbing, heat and air-conditioning installation",
                  "likelihood": 0.2
                }
              ],
              "reasoning": "The respondent's data indicates electrical work but needs clarification on specific installation type..."
            },
            {
              "type": "soc",
              "classified": true,
              "followup": null,
              "code": "5245",
              "description": "Electricians and electrical fitters",
              "candidates": [
                {
                  "code": "5245",
                  "descriptive": "Electricians and electrical fitters",
                  "likelihood": 0.95
                }
              ],
              "reasoning": "The respondent's data clearly indicates electrical work activities..."
            }
          ]
        }
      ]
    }
  ]
}
```

## Data Models

### Generic Classification Models

- `GenericCandidate`: Represents a classification candidate with code, description, and likelihood
- `GenericClassificationResult`: Represents a single classification result with type, status, and candidates
- `GenericClassificationResponse`: The main response containing requested type and results array

## Implementation Notes

1. **SOC Classification**: Currently uses a placeholder implementation. Full SOC classification will be implemented using the SOC LLM client from the `soc-classification-utils` package.

2. **Vector Store Clients**: Separate clients are used for SIC and SOC vector stores:
   - SIC: `SICVectorStoreClient` (port 8088)
   - SOC: `SOCVectorStoreClient` (port 8089)

3. **LLM Integration**: The implementation supports both SIC and SOC LLM clients, with proper separation of concerns.

4. **Error Handling**: Comprehensive error handling is implemented for both classification types.

5. **Rephrasing**: SIC candidates are automatically rephrased using the `SICRephraseClient` when available.

## Testing

Comprehensive tests have been added to verify:
- SIC-only classification
- SOC-only classification  
- Combined SIC+SOC classification
- Error handling for invalid inputs
- Rephrasing functionality

## Future Enhancements

1. **Full SOC Implementation**: Replace placeholder SOC classification with full LLM-based classification
2. **Rephrasing Support**: Extend rephrasing functionality to work with SOC classification results
3. **Performance Optimization**: Optimize vector store queries for combined classification
4. **Additional Classification Types**: Extend the framework to support other classification systems 