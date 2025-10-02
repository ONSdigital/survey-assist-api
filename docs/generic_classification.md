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
  "llm": "gemini-2.5-flash",
  "type": "sic|soc|sic_soc",
  "job_title": "string",
  "job_description": "string",
  "org_description": "string (optional)",
  "options": {
    "rephrased": true|false
  }
}
```

**Request Parameters:**

- `llm` (required): The LLM model to use for classification
- `type` (required): Type of classification (`sic`, `soc`, or `sic_soc`)
- `job_title` (required): Survey response for Job Title
- `job_description` (required): Survey response for Job Description  
- `org_description` (optional): Survey response for Organisation / Industry Description
- `options` (optional): Classification options
  - `rephrased` (optional): Whether to apply rephrasing to classification results. Defaults to `true` for backward compatibility.

## Rephrasing Feature

The API supports rephrasing of classification descriptions to provide more user-friendly versions. This feature can be controlled separately for SIC and SOC classifications.

### How Rephrasing Works

The rephrase toggle allows you to choose between:
- **Original SIC descriptions**: Technical, official SIC code descriptions
- **Rephrased descriptions**: User-friendly, simplified versions of the same information

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

If no `options` are provided, rephrasing defaults to `true` for both SIC and SOC to maintain backward compatibility.

### Rephrasing Examples

| SIC Code | Original Description | Rephrased Description |
|----------|---------------------|----------------------|
| 01110 | "Growing of cereals (except rice), leguminous crops and oil seeds" | "Crop growing" |
| 01410 | "Raising of dairy cattle" | "Dairy farming" |
| 01450 | "Raising of sheep and goats" | "Sheep and goat farming" |
| 01500 | "Mixed farming" | "Crop and livestock farm" |

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

**Expected Response:** Shows rephrased descriptions (e.g., "Crop growing")

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

**Expected Response:** Shows rephrased descriptions (same as default)

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

**Expected Response:** Shows original descriptions (e.g., "Growing of cereals (except rice), leguminous crops and oil seeds")

#### Granular Control (SIC Rephrased, SOC Not Rephrased)

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
- SIC results show rephrased descriptions
- SOC results show original descriptions (when SOC rephrasing is implemented)

### Data Coverage Note

The rephrase data currently contains **only agricultural SIC codes (01xxx series)** such as crop farming, dairy farming, and livestock raising. For all other SIC codes (industrial, construction, healthcare, retail, etc.), the toggle will show the same descriptions regardless of setting, as no rephrased versions are available.
