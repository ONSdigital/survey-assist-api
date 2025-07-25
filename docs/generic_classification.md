# Generic Classification API

This document describes the new generic classification functionality that supports both SIC (Standard Industrial Classification) and SOC (Standard Occupational Classification) in a unified API.

## Overview

The Survey Assist API has been enhanced to support generic classification responses that can handle both SIC and SOC classification types. This allows for more flexible and extensible classification capabilities while maintaining backward compatibility.

## New Endpoints

### Generic Classification Endpoint

**POST** `/v1/survey-assist/classify/v2`

This endpoint provides the new generic classification functionality that can handle SIC, SOC, or combined SIC+SOC classification.

#### Request Format

```json
{
  "llm": "gemini",
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

### Generic Result Storage Endpoints

**POST** `/v1/survey-assist/result/v2`

Store generic survey results that can contain SIC and/or SOC classification data.

**GET** `/v1/survey-assist/result/v2`

Retrieve generic survey results.

## Examples

### SIC Classification Only

**Request:**
```json
{
  "llm": "gemini",
  "type": "sic",
  "job_title": "Farm Hand",
  "job_description": "I work on a farm tending crops that are harvested and sold to wholesalers",
  "org_description": "A farm that grows and harvests crops to be sold to wholesalers"
}
```

**Response:**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": false,
      "followup": "What types of crops does the farm primarily grow and harvest?",
      "code": "01110",
      "description": "Growing of cereals (except rice), legumes and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Growing of cereals (except rice), legumes and oil seeds",
          "likelihood": 0.7
        },
        {
          "code": "01120",
          "descriptive": "Growing of rice",
          "likelihood": 0.1
        }
      ],
      "reasoning": "The respondent's data indicates a farm growing and harvesting crops for sale to wholesalers..."
    }
  ]
}
```

### SOC Classification Only

**Request:**
```json
{
  "llm": "gemini",
  "type": "soc",
  "job_title": "Farm Hand",
  "job_description": "I work on a farm tending crops that are harvested and sold to wholesalers",
  "org_description": "A farm that grows and harvests crops to be sold to wholesalers"
}
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
      "reasoning": "The respondent's data indicates..."
    }
  ]
}
```

### Combined SIC and SOC Classification

**Request:**
```json
{
  "llm": "gemini",
  "type": "sic_soc",
  "job_title": "Farm Hand",
  "job_description": "I work on a farm tending crops that are harvested and sold to wholesalers",
  "org_description": "A farm that grows and harvests crops to be sold to wholesalers"
}
```

**Response:**
```json
{
  "requested_type": "sic_soc",
  "results": [
    {
      "type": "sic",
      "classified": false,
      "followup": "What types of crops does the farm primarily grow and harvest?",
      "code": "01110",
      "description": "Growing of cereals (except rice), legumes and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Growing of cereals (except rice), legumes and oil seeds",
          "likelihood": 0.7
        }
      ],
      "reasoning": "The respondent's data indicates a farm growing and harvesting crops..."
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
      "reasoning": "The respondent's data indicates..."
    }
  ]
}
```

## Backward Compatibility

The original classification endpoint (`/v1/survey-assist/classify`) remains unchanged and continues to work as before. The new generic functionality is available through the `/v1/survey-assist/classify/v2` endpoint.

## Data Models

### Generic Classification Models

- `GenericCandidate`: Represents a classification candidate with code, description, and likelihood
- `GenericClassificationResult`: Represents a single classification result with type, status, and candidates
- `GenericClassificationResponse`: The main response containing requested type and results array

### Generic Result Models

- `GenericSurveyAssistInteraction`: Interaction model that can handle SIC/SOC classification results
- `GenericResponse`: Response model for generic survey data
- `GenericSurveyAssistResult`: Complete survey result model for generic classification

## Implementation Notes

1. **SOC Classification**: Currently uses a placeholder implementation. Full SOC classification will be implemented using the SOC LLM client from the `soc-classification-utils` package.

2. **Vector Store Clients**: Separate clients are used for SIC and SOC vector stores:
   - SIC: `SICVectorStoreClient` (port 8088)
   - SOC: `SOCVectorStoreClient` (port 8089)

3. **LLM Integration**: The implementation supports both SIC and SOC LLM clients, with proper separation of concerns.

4. **Error Handling**: Comprehensive error handling is implemented for both classification types.

## Testing

Comprehensive tests have been added to verify:
- SIC-only classification
- SOC-only classification  
- Combined SIC+SOC classification
- Error handling for invalid inputs
- Generic result storage and retrieval

## Future Enhancements

1. **Full SOC Implementation**: Replace placeholder SOC classification with full LLM-based classification
2. **Rephrasing Support**: Extend rephrasing functionality to work with generic classification results
3. **Performance Optimization**: Optimize vector store queries for combined classification
4. **Additional Classification Types**: Extend the framework to support other classification systems 