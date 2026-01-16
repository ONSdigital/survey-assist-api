# Generic Classification API

This document describes the generic classification functionality that supports both SIC (Standard Industrial Classification) and SOC (Standard Occupational Classification) in a unified API.

## Overview

The Survey Assist API supports generic classification responses that can handle both SIC and SOC classification types. This allows for more flexible and extensible classification capabilities while maintaining backward compatibility.

### Classification Process

The classification process works as follows:

1. **Vector Store Search**: The input text (job title, job description, organisation description) is used to search the vector store for a list of candidate classification codes.

2. **Unambiguous Classification**: The LLM first attempts to find an **unambiguous** classification from the candidates.

3. **Definitive Match**: If a definitive code is found, the API returns a response with `classified: true`, the found code and description, and `followup: null`.

4. **Ambiguous Result**: If the result is ambiguous and a definitive code cannot be determined, the LLM formulates a **follow-up question** to gather more information. The API returns a response with `classified: false`, no code/description, and the `followup` question populated.

### Current Implementation Status

- **SIC Classification**: ✅ Fully implemented with vector store search, LLM classification, and rephrasing support
- **SOC Classification**: ⚠️ Placeholder implementation - returns hardcoded result (code "9111", description "Farm workers") regardless of input. Full implementation planned for future releases.

## Endpoints

### Generic Classification Endpoint

**POST** `/v1/survey-assist/classify`

This endpoint provides generic classification functionality that can handle SIC, SOC, or combined SIC+SOC classification.

### Result Storage Endpoints

The API provides endpoints for storing and retrieving survey results that can contain SIC and/or SOC classification data:

**POST** `/v1/survey-assist/result`

Store survey results in Firestore. Requires `FIRESTORE_DB_ID` environment variable to be set. Returns a Firestore document ID.

**GET** `/v1/survey-assist/result?result_id=<document_id>`

Retrieve a stored survey result from Firestore by document ID. Requires `FIRESTORE_DB_ID` environment variable to be set.

**GET** `/v1/survey-assist/results?survey_id=<id>&wave_id=<id>&case_id=<id>`

List stored survey results filtered by survey_id, wave_id, and optionally case_id. Requires `FIRESTORE_DB_ID` environment variable to be set.

**Note:** The result storage endpoints support both the legacy format (with `survey_assist_interactions` containing `flavour: "sic"` or `flavour: "soc"`) and the generic format (with `GenericSurveyAssistResult` containing `GenericClassificationResult` objects with `type: "sic"` or `type: "soc"`).

#### Request Format

```json
{
  "llm": "gemini",
  "type": "sic|soc|sic_soc",
  "job_title": "string",
  "job_description": "string",
  "org_description": "string (optional)",
  "options": {
    "sic": {
      "rephrased": true|false
    },
    "soc": {
      "rephrased": true|false
    }
  }
}
```

**Request Parameters:**

- `llm` (required): The LLM model to use for classification. Valid values: `"gemini"` or `"chat-gpt"`. **Note:** Only `"gemini"` is currently implemented - the API always uses "gemini-2.5-flash" regardless of this value. The `"chat-gpt"` option is accepted but not yet implemented.
- `type` (required): Type of classification (`sic`, `soc`, or `sic_soc`)
- `job_title` (required): Survey response for Job Title
- `job_description` (required): Survey response for Job Description  
- `org_description` (optional): Survey response for Organisation / Industry Description
- `options` (optional): Classification options object
  - `sic` (optional): SIC-specific options
    - `rephrased` (boolean, default: `true`): Whether to apply rephrasing to SIC classification results
  - `soc` (optional): SOC-specific options
    - `rephrased` (boolean, default: `true`): Whether to apply rephrasing to SOC classification results (not yet implemented)

**Note**: If `options` is not provided, rephrasing defaults to `true` for both SIC and SOC to maintain backward compatibility.

#### Response Format

The endpoint returns a generic classification response that can contain one or more classification results:

**Without options (no meta field):**
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

**With options (includes meta field):**
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
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {
        "rephrased": true|false
      },
      "soc": {
        "rephrased": true|false
      }
    }
  }
}
```

**Response Fields:**

- `requested_type` (string): The type of classification that was requested ("sic", "soc", or "sic_soc")
- `results` (array): List of classification results, one for each type requested
  - `type` (string): The classification type ("sic" or "soc")
  - `classified` (boolean): Whether the input could be definitively classified
  - `followup` (string|null): Additional question to help classify (only present if `classified=false`)
  - `code` (string|null): The classification code (only present if `classified=true`)
  - `description` (string|null): The classification description (only present if `classified=true`)
  - `candidates` (array): List of potential classification candidates with code, descriptive, and likelihood
  - `reasoning` (string): Reasoning behind the classification
- `meta` (object, optional): Response metadata, only included when `options` were provided in the request
  - `llm` (string): The LLM model used
  - `applied_options` (object): The options that were applied
    - `sic` (object, optional): Applied SIC options
    - `soc` (object, optional): Applied SOC options

**Important Notes:**
- **SOC Classification**: Currently a placeholder implementation. Requests with `type="soc"` or `type="sic_soc"` will return a placeholder SOC result with code "9111" and description "Farm workers". Full SOC classification support is planned for future releases.
- **Meta Field**: The `meta` field is only included in the response when `options` are provided in the request. This allows clients to see which options were actually applied.

## Rephrasing Feature

The API supports rephrasing of classification descriptions to provide more user-friendly versions. This feature can be controlled separately for SIC and SOC classifications.

### How Rephrasing Works

The rephrase toggle controls whether rephrased descriptions appear in the `candidates` array:
- **When `rephrased: true`**: The `candidates[].descriptive` field contains user-friendly, simplified versions of the SIC code descriptions
- **When `rephrased: false`**: The `candidates[].descriptive` field contains the original technical, official SIC code descriptions

**Important:** The main `description` field in the result always shows the original description, regardless of the rephrasing setting. Rephrased descriptions only appear in the `candidates` array.

### Rephrasing Data Sources

**Package Data**: Contains 28 agricultural SIC codes (01xxx series) with rephrased descriptions
**Local Data**: Contains full rephrase dataset with comprehensive coverage

The rephrase data source is controlled by the `SIC_REPHRASE_DATA_PATH` environment variable, just like the lookup data.

### Options Structure

The `options` field allows granular control over rephrasing for different classification types:

```json
{
  "options": {
    "sic": {
      "rephrased": true
    },
    "soc": {
      "rephrased": false
    }
  }
}
```

### Rephrasing Controls

- **SIC Rephrasing**: ✅ **Fully implemented and functional**
- **SOC Rephrasing**: 🔄 **Not yet implemented** (placeholder for future development)

### Default Behaviour

If no `options` are provided:
- Rephrasing defaults to `true` for both SIC and SOC to maintain backward compatibility
- The `meta` field is not included in the response
- Rephrased descriptions appear in the `candidates` array when available

If `options` are provided:
- The `meta` field is included in the response showing which options were applied
- Rephrasing settings are applied as specified in the request

### Rephrasing Examples

When rephrasing is enabled, the `candidates[].descriptive` field contains the rephrased version:

| SIC Code | Original Description (in `description` field) | Rephrased Description (in `candidates[].descriptive` when `rephrased: true`) |
|----------|-----------------------------------------------|--------------------------------------------------------------------------------|
| 01110 | "Growing of cereals (except rice), leguminous crops and oil seeds" | "Crop growing" |
| 01410 | "Raising of dairy cattle" | "Dairy farming" |
| 01450 | "Raising of sheep and goats" | "Sheep and goat farming" |
| 01500 | "Mixed farming" | "Crop and livestock farm" |

**Note:** The main `description` field always contains the original description. Only the `candidates` array reflects the rephrasing setting.

### Examples

#### Default Behaviour (Rephrasing Enabled)

```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Farmer",
    "job_description": "Growing cereals and crops",
    "org_description": "Agricultural farm"
  }'
```

**Expected Response (no meta field since options not provided):**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "01110",
      "description": "Growing of cereals (except rice), leguminous crops and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Crop growing",
          "likelihood": 0.95
        }
      ],
      "reasoning": "Based on the job title and description..."
    }
  ]
}
```

**Note:** Even though rephrasing is enabled by default, the main `description` field shows the original description. The rephrased version appears in the `candidates` array under `descriptive`.

#### Explicitly Enable SIC Rephrasing

```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Farmer",
    "job_description": "Growing cereals and crops",
    "org_description": "Agricultural farm",
    "options": {
      "sic": {
        "rephrased": true
      }
    }
  }'
```

**Expected Response (includes meta field since options provided):**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "01110",
      "description": "Growing of cereals (except rice), leguminous crops and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Crop growing",
          "likelihood": 0.95
        }
      ],
      "reasoning": "Based on the job title and description..."
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {
        "rephrased": true
      }
    }
  }
}
```

**Note:** Rephrased descriptions appear in the `candidates` array. The main `description` field always shows the original description.

#### Explicitly Disable SIC Rephrasing

```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic",
    "job_title": "Farmer",
    "job_description": "Growing cereals and crops",
    "org_description": "Agricultural farm",
    "options": {
      "sic": {
        "rephrased": false
      }
    }
  }'
```

**Expected Response:**
```json
{
  "requested_type": "sic",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "01110",
      "description": "Growing of cereals (except rice), leguminous crops and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Growing of cereals (except rice), leguminous crops and oil seeds",
          "likelihood": 0.95
        }
      ],
      "reasoning": "Based on the job title and description..."
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {
        "rephrased": false
      }
    }
  }
}
```

**Note:** When rephrasing is disabled, both the main `description` and the `candidates[].descriptive` fields show the original description.

#### Combined SIC and SOC Classification

```bash
curl -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": "gemini",
    "type": "sic_soc",
    "job_title": "Farmer",
    "job_description": "Growing cereals and crops",
    "org_description": "Agricultural farm",
    "options": {
      "sic": {
        "rephrased": true
      },
      "soc": {
        "rephrased": false
      }
    }
  }'
```

**Expected Response:**
```json
{
  "requested_type": "sic_soc",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "01110",
      "description": "Growing of cereals (except rice), leguminous crops and oil seeds",
      "candidates": [
        {
          "code": "01110",
          "descriptive": "Crop growing",
          "likelihood": 0.95
        }
      ],
      "reasoning": "Based on the job title and description..."
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
      "reasoning": "Placeholder SOC classification reasoning"
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {
        "rephrased": true
      },
      "soc": {
        "rephrased": false
      }
    }
  }
}
```

**Note:** 
- SIC results show rephrased descriptions in the `candidates` array when rephrasing is enabled
- SOC classification is currently a placeholder implementation and will always return code "9111" with description "Farm workers" regardless of input
- SOC rephrasing is not yet implemented, so the `rephrased` option for SOC has no effect currently

### Data Coverage Note

The rephrase data currently contains **only agricultural SIC codes (01xxx series)** such as crop farming, dairy farming, and livestock raising. 

**Default Package Data:** Contains 28 agricultural SIC codes with rephrased descriptions from the `industrial_classification.data` package.

**Custom Data:** You can override with a full dataset by setting the `SIC_REPHRASE_DATA_PATH` environment variable.

For SIC codes outside the agricultural series (industrial, construction, healthcare, retail, etc.), the `candidates[].descriptive` field will show the same original description regardless of the `rephrased` setting, as no rephrased versions are available for those codes.
