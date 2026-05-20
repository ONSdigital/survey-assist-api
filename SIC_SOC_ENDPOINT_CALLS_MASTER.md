# SIC + SOC Comprehensive Local Call Test Runbook

**Last full SIC run:** 2026-04-28 14:33:37  
**Last SOC / SA-693 run:** 2026-05-19 (two-step classify verified live; farm hand + vague Worker case; see caveat below)

This runbook consolidates and extends coverage from:
- `SA-693-task.md` (two-step SOC classify)
- `SOC_REPHRASE_MANUAL_TEST.md`
- `SA-649-live-curl-results.md`
- `SA-673-local-api-test-results.md`
- `SA-559-soc-lookup-testing.md`
- `README.md`, `docs/index.md`, and `docs/guide.md`

## SA-693 — SOC classify (two-step)

SOC classify on `POST /v1/survey-assist/classify` (`type`: `soc` or `sic_soc`) now mirrors SIC:

1. SOC vector store search → short list (`code`, `title`, `distance`).
2. **`unambiguous_soc_code`** — if `codable` and `class_code` set → `classified: true`, `followup: null`, final `code` / `description`.
3. Else **`formulate_open_question`** — `classified: false`, non-null `followup`, `code` / `description` null; candidates from step 2.

Removed from the API: SA-673 clear-winner promotion (`_select_soc_clear_winner`). Classify does **not** call `sa_rag_soc_code`.

### Prerequisites (local)

```bash
# survey-assist-api — path dep to SA-693 utils on branch SA-693/two-step-classify
cd survey-assist-api && poetry install

export SOC_VECTOR_STORE="http://localhost:8089"
export SOC_LOOKUP_DATA_PATH="data/soc_knowledge_base_utf8_SA-649.csv"
export SOC_REPHRASE_DATA_PATH="data/soc_rephrased_2026_04_17_nec_only.csv"

# Gemini / Vertex (required for classify)
gcloud auth application-default login

# Terminal 1: soc-classification-vector-store
make run-vector-store   # port 8089

# Terminal 2: survey-assist-api (restart after poetry install)
make run-api            # port 8080
```

Run the curl commands in the sections below (for example `CLASSIFY_SOC_UNAMBIGUOUS`, `SOC_VS_STATUS`). For SOC-only testing, skip `CLASSIFY_SIC_SOC` unless the SIC vector store is running on port **8088**.

**Gemini auth:** run `gcloud auth application-default login` in your terminal, then **restart** `make run-api` in the same session (or export ADC in the shell that starts uvicorn). Without valid ADC, startup logs show `RefreshError` and `soc_llm` stays unset.

### SA-693 acceptance checks (classify)

| Case | Expected |
|---|---|
| `CLASSIFY_SOC_UNAMBIGUOUS` (farm hand) | HTTP `200`, `classified: true`, `code: "9111"`, `followup: null` |
| `CLASSIFY_SOC_AMBIGUOUS` / finance manager | HTTP `200`, `classified: false`, non-empty `followup`, `code: null` (see caveat) |
| `CLASSIFY_SOC_REPHRASE_*` | Same branching; rephrase only affects text passed to vector search / LLM |
| `CLASSIFY_SIC_SOC` | SIC result unchanged; SOC leg uses two-step flow |

**Caveat — finance manager is not a reliable live test for step 2:** On 2026-05-19, live Gemini often returned `codable: true` from `unambiguous_soc_code` for the finance-manager payload (`classified: true`, `code: "1131"`, only one LLM call in API logs). That matches SIC: step 2 runs when the first LLM sets `codable: false`, not when candidate likelihoods are close. To verify `formulate_open_question` live, use a genuinely vague job (for example `job_title: "Worker"`, `job_description: "I do various tasks depending on what is needed each day"`) or rely on `test_soc_not_codable_returns_followup` in `tests/test_classify.py` (mocked `codable: false`).

## Scope

Covers local call behaviour for:
- SIC lookup endpoint (`/v1/survey-assist/sic-lookup`) – exact, similarity, validation, unknown
- SOC lookup endpoint (`/v1/survey-assist/soc-lookup`) – exact, similarity, validation, unknown
- SOC vector store (`/v1/soc-vector-store/status`, search used by classify)
- Classification endpoint (`/v1/survey-assist/classify`) – `sic`, `soc`, `sic_soc`, options on/off, validation
- Supporting service checks (`/`, `/config`, `/embeddings`)

## Expected Non-200 Cases

These are intentional validation checks in this suite and should not be treated as platform failures:
- `SIC_LOOKUP_EMPTY` returns `400 Bad Request` (empty `description`)
- `SOC_LOOKUP_EMPTY` returns `400 Bad Request` (empty `description`)
- `SOC_LOOKUP_UNKNOWN` returns `404 Not Found` (no matching SOC code)
- `CLASSIFY_INVALID_TYPE` returns `422 Unprocessable Entity` (`type` must be `sic`, `soc`, or `sic_soc`)

## Summary

| Case | Method | HTTP (expected) | Notes |
|---|---|---:|---|
| `ROOT_HEALTH` | `GET` | `200` | |
| `CONFIG` | `GET` | `200` | |
| `EMBEDDINGS` | `GET` | `200` | SIC vector store |
| `SIC_LOOKUP_*` | `GET` | see SIC sections | unchanged |
| `SOC_VS_STATUS` | `GET` | `200` | `http://localhost:8089` |
| `SOC_LOOKUP_EXACT` | `GET` | `200` | 2026-05-19 verified |
| `SOC_LOOKUP_SIMILARITY` | `GET` | `200` | 2026-05-19 verified |
| `SOC_LOOKUP_EMPTY` | `GET` | `400` | 2026-05-19 verified |
| `SOC_LOOKUP_UNKNOWN` | `GET` | `404` | was `200` in 2026-04 run |
| `CLASSIFY_SIC_*` | `POST` | `200` | SIC sections below (2026-04) |
| `CLASSIFY_SOC_UNAMBIGUOUS` | `POST` | `200` | SA-693 farm hand → `9111` |
| `CLASSIFY_SOC_AMBIGUOUS` | `POST` | `200` | SA-693 step 2 — finance manager often codable; see caveat |
| `CLASSIFY_SOC_REPHRASE_FALSE` | `POST` | `200` | re-run after SA-693 |
| `CLASSIFY_SOC_REPHRASE_TRUE` | `POST` | `200` | re-run after SA-693 |
| `CLASSIFY_SOC_DEFAULT` | `POST` | `200` | default rephrase on |
| `CLASSIFY_SIC_SOC` | `POST` | `200` | **skip** unless SIC vector store on `:8088` is running |
| `CLASSIFY_INVALID_TYPE` | `POST` | `422` | |

## ROOT_HEALTH

API root availability

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/"
```

Result: HTTP `200` in `0.001280` seconds

Response body:

```json
{
  "message": "Survey Assist API is running"
}
```

## CONFIG

Config endpoint returns runtime settings

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/config"
```

Result: HTTP `200` in `8.839051` seconds

Response body:

```json
{
  "llm_model": "gemini-2.5-flash",
  "data_store": "Firestore",
  "firestore_database_id": "survey-assist-db",
  "v1v2": {
    "classification": [
      {
        "type": "sic",
        "prompts": [
          {
            "name": "SA_SIC_PROMPT_RAG",
            "text": "You are a conscientious classification assistant of respondent data\nfor the use in the UK official statistics. Respondent data may be in English or Welsh,\nbut you always respond in British English.\"Given the respondent's description of the main activity their\ncompany does, their job title and job description (which may be different to the\nmain company activity), your task is to determine a list of the most likely UK SIC\n(Standard Industry Classification) codes for this company and the final code\nthat is most likely to match the description.\n\nThe following will be provided to make your decision and send appropriate output:\nRespondent Data\nRelevant subset of UK SIC 2007 (you must only use this list to classify)\nOutput Format (the output format MUST be valid JSON)\n\nOnly use the subset of UK SIC 2007 provided to determine if you can match the most\nlikely sic codes, provide a confidence score between 0 and 1 where 0.1 is least\nlikely and 0.9 is most likely.\n\nYou must return a subset list of possible sic codes (UK SIC 2007 codes provided)\nthat might match with a confidence score for each.\n\nYou must provide a follow up question that would help identify the exact coding based\non the list you respond with.\n\nAlways provide reasoning for your decision.\n\n\n===Respondent Data===\n- Company's main activity: {industry_descr}\n- Job Title: {job_title}\n- Job Description: {job_description}\n\n===Relevant subset of UK SIC 2007===\n{sic_index}\n\n===Output Format===\n{format_instructions}\n\n===Output===\n"
          }
        ]
      }
    ]
  },
  "v3": {
    "classification": [
      {
        "type": "sic",
        "prompts": [
          {
            "name": "SIC_PROMPT_RERANKER",
            "text": "You are a conscientious classification assistant of respondent data\nfor the use in the UK official statistics. Respondent data may be in English or Welsh,\nbut you always respond in British English.\"You are a precise semantic matching system.\nYour task is to re-rank and select the N most relevant UK SIC (Standard Industry\nClassification) codes from a provided list of candidates based on their relevance\nto the respondent's description.\n\n===Task Description===\n\nAnalyze each candidate SIC code's relevance to the query.\nScore each candidate on a scale of 0.0 to 1.0 based on semantic similarity and\nbusiness context alignment.\nSelect the top N most relevant codes.\nProvide clear reasoning for your scoring decisions.\nYour response must be a single JSON object with NO additional text or formatting.\n\n===Scoring Criteria===\n\nPrimary Activity Match (0.0-0.4):\n\nEvaluates the fundamental alignment between the query and the code's main\nbusiness activity\n\nScoring guidelines:\n\n0.35-0.4: Perfect match (e.g., \"Beer brewery\" → \"Manufacture of beer\")\n0.25-0.34: Strong match with minor differences (e.g., \"Craft brewery\" →\n\"Manufacture of beer\")\n0.15-0.24: Related activity in same sector (e.g., \"Beer distribution\" →\n\"Manufacture of beer\")\n0.05-0.14: Tangentially related activity (e.g., \"Beer tasting\" →\n\"Manufacture of beer\")\n0.0-0.04: Minimal or no relation to primary activity\n\n\nContext Precision (0.0-0.3):\n\nMeasures how specifically the code captures the business context of the query\nConsiders industry position (manufacturing, wholesale, retail, service)\nScoring guidelines:\n\n0.25-0.3: Exact business context match (e.g., manufacturing vs. retail context)\n0.15-0.24: Related context with same business model\n0.05-0.14: Similar industry but different business model\n0.0-0.04: Different business context entirely\n\n\nExamples:\n\nQuery \"Beer shop\" matching \"Retail sale of beverages\" (high precision)\nQuery \"Beer shop\" matching \"Wholesale of beverages\" (medium precision)\nQuery \"Beer shop\" matching \"Manufacture of beer\" (low precision)\n\n\nExample Activity Alignment (0.0-0.3):\n\nEvaluates matches between query and specific example activities listed under the code\nConsiders both exact matches and semantic similarity\n\nScoring guidelines:\n\n0.25-0.3: Direct match with example activities\n0.15-0.24: Semantic equivalence to example activities\n0.05-0.14: Partial overlap with example activities\n0.0-0.04: No matching example activities\n\n\nSpecial considerations:\n\nMultiple matching examples increase score within range\nIndustry-specific terminology matches are weighted heavily\nGeneric matches receive lower scores\n\n===Input Data===\n- Company's main activity: {industry_descr}\n- Job Title: {job_title}\n- Job Description: {job_description}\n- Number of codes to select (N): {n}\n\n===UK SIC 2007 candidates===\n{sic_index}\n\n===Requirements===\n\nScores must be between 0.0 and 1.0\nSe
... (truncated)
```

## EMBEDDINGS

Vector-store connectivity/status check

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/embeddings"
```

Result: HTTP `200` in `2.771733` seconds

Response body:

```json
{
  "status": "ready",
  "embedding_model_name": "all-MiniLM-L6-v2",
  "llm_model_name": "",
  "db_dir": "src/sic_classification_vector_store/data/vector_store",
  "sic_index_file": "('sic_classification_vector_store.data.sic_index', 'uksic2007indexeswithaddendumdecember2022.xlsx')",
  "sic_structure_file": "('sic_classification_vector_store.data.sic_index', 'publisheduksicsummaryofstructureworksheet.xlsx')",
  "sic_condensed_file": "('industrial_classification_utils.data.example', 'sic_2d_condensed.txt')",
  "matches": 20,
  "index_size": 16618
}
```

## SIC_LOOKUP_EXACT

SIC exact lookup

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=electrical%20installation&similarity=false"
```

Result: HTTP `200` in `0.001138` seconds

Response body:

```json
{
  "description": "electrical installation",
  "code": "43210",
  "code_meta": {
    "code": "4321x",
    "title": "Electrical installation",
    "detail": "This class includes the installation of electrical systems in all kinds of buildings and civil engineering structures of electrical systems.",
    "includes": [
      "installation of: electrical wiring and fittings telecommunications wiring computer network and cable television wiring, including fibre optic satellite dishes lighting systems fire alarms burglar alarm systems street lighting and electrical signals airport runway lighting electric solar energy collectors",
      "connecting of electric appliances and household equipment, including baseboard heating"
    ],
    "excludes": [
      "construction of communications and power transmission lines, see ##42.22",
      "monitoring and remote monitoring of electronic security systems, such as burglar alarms and fire alarms, including their installation and maintenance, see ##80.20"
    ]
  },
  "code_division": "43",
  "code_division_meta": {
    "code": "43xxx",
    "title": "Specialised construction activities",
    "detail": "This division includes specialised construction activities (special trades), i.e. the construction, or preparation for construction, of parts of buildings and civil engineering works. These activities are usually specialised in one aspect common to different structures, requiring specialised skills or equipment, such as pile-driving, foundation work, carcass work, concrete work, brick laying, stone setting, scaffolding, roof covering, etc. The erection of steel structures is included provided that the parts are not produced by the same unit. Specialised construction activities are mostly carried out under subcontract, but especially in repair construction it is done directly for the owner of the property.<BR><BR>Also included are building finishing and building completion activities.<BR><BR>Included is the installation of all kind of utilities that make the construction function as such. These activities are usually performed at the site of the construction, although parts of the job may be carried out in a special shop. Included are activities such as plumbing, installation of heating and air-conditioning systems, antennas, alarm systems and other electrical work, sprinkler systems, elevators and escalators, etc. Also included are insulation work (water, heat, sound), sheet metal work, commercial refrigerating work, the installation of illumination and signalling systems for roads, railways, airports, harbours, etc. Repair of the above mentioned installations is also included.<BR><BR>Building completion activities encompass activities that contribute to the completion or finishing of a construction such as glazing, plastering, painting, floor and wall tiling or covering with other materials like parquet, carpets, wallpaper, etc., floor sanding, finish carpentry, acoustical work, cleaning of the exterior, etc. Repairs to the above mentioned completion or finishing work are also included.<BR><BR>The renting of equipment with operator is classified with the associated construction activity.",
    "includes": [],
    "excludes": []
  }
}
```

## SIC_LOOKUP_SIMILARITY

SIC similarity lookup

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=electrical&similarity=true"
```

Result: HTTP `200` in `0.008356` seconds

Response body:

```json
{
  "description": "electrical",
  "code": null,
  "code_meta": null,
  "code_division": null,
  "code_division_meta": null,
  "potential_matches": {
    "descriptions_count": 278,
    "descriptions": [
      "domestic heating and cooking appliances (non-electrical)",
      "basic electrical equipment and machinery",
      "batteries, accumulators and industrial electrical equipment",
      "electrical instruments and appliances for measuring, checking, testing and navigating",
      "electrical measuring equipment, radio etc",
      "motor vehicle parts (except electrical, glass or rubber)",
      "non-electrical measuring, checking and precision instruments and apparatus",
      "motor vehicle repair and maintenance (including body work and electrical)",
      "radios, record players etc, electrical goods and appliances (not rental)",
      "electrical and mechanical engineers",
      "general mechanical and electrical engineering services",
      "electrical motor rewinds",
      "manufacture of electrical transformers",
      "manufacture of electrical transformers using copper steel",
      "electrical control gear manufacture",
      "electrical switchgear manufacture",
      "manufacture of electrical switchboards",
      "manufacture of medium high voltage electrical switchgear and protection products",
      "repair of electrical switch gear",
      "manufacture of electrical distribution equipment",
      "optical fibre and electrical cable manufacturer",
      "manufacture automotive electrical equipment",
      "manufacture maintenance and installation of electrical equipment",
      "manufacture of electrical emergency and fire alarm equipment",
      "distribution and manufacture of electrical and electronic components",
      "manufacturing electrical test equipment",
      "calibration and repair of mechanical and electrical measuring instrumentation",
      "assembly of electrical control panels",
      "manufacturer of industrial process electrical control panels",
      "distribution of electrical energy",
      "civil engineering construction and installation of electrical cables and fitters",
      "construction electrical contracting",
      "domestic and commercial electrical contractors",
      "domestic and industrial electrical contractor",
      "electrical contracting and engineering",
      "electrical contracting and maintenance",
      "electrical contracting and repairs",
      "electrical contracting cable jointing",
      "electrical contracting industry",
      "electrical contracting work",
      "electrical contractor",
      "electrical contractors and engineers",
      "electrical contractors and retailers",
      "electrical contractors and wholesalers",
      "electrical contractors for the exhibition industry",
      "electrical engineering",
      "electrical fitter",
      "electrical installation contracting",
      "electrical installation contractors",
      "electrical contractor and shop fitting contractor",
      "electrical installers",
      "electrical maintenance",
      "electrical services",
      "electrical subcontractors",
      "electrical wiring",
      "electrical wiring and fittings",
      "electrical work",
      "electrical installation contractors computer and data cabling installers",
      "general electrical contractor maintenance",
      "installation and testing of electrical wiring and fittings",
      "installation of electrical building services",
      "installation of electrical cctv equipment",
      "installation of electrical equipment cables and troughing",
      "installation of electrical wiring",
      "installation of electrical wiring and fittings control systems motor rewinds",
      "installation of electrical wiring fittings and electrical maintenance",
      "maintenance installation of electrical equipment",
      "rewiring and electrical fittings in new houses",
      "installation and maintenance of security systems electrical contracting",
      "auto electrical engineers",
      "auto electrical repairs",
      "auto electrical services",
      "auto electrical specialists",
      "auto electrical and fuel injection specialists",
      "car electrical repairs",
      "motor vehicle repairs mechanical and electrical",
      "auto electrical distributors vehicle bulbs cable terminal accessories",
      "electrical and plumbing contractors",
      "electrical plumbing and heating contractors",
      "gas and electrical engineer including technical testing and analysis",
      "heating and electrical engineers",
      "plumbing heating electrical",
      "distributor of electrical household appliances",
      "household electrical and electronic distributors",
      "wholesale distributor of domestic electrical goods",
      "wholesale of electrical household appliances",
      "wholesale of electrical household goods to retail outlets",
      "wholesale of radio television and electrical household appliances",
      
... (truncated)
```

## SIC_LOOKUP_EMPTY

SIC lookup validation error path (expected 400)

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=&similarity=false"
```

Result: HTTP `400` in `0.000886` seconds

Response body:

```json
{
  "detail": "Description cannot be empty"
}
```

## SIC_LOOKUP_UNKNOWN

SIC lookup unknown description path

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/sic-lookup?description=zzzxxyyqq&similarity=false"
```

Result: HTTP `200` in `0.001308` seconds

Response body:

```json
{
  "description": "zzzxxyyqq",
  "code": null,
  "code_meta": null,
  "code_division": null,
  "code_division_meta": null
}
```

## SOC_LOOKUP_EXACT

SOC exact lookup

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/soc-lookup?description=zoologist&similarity=false"
```

Result: HTTP `200` in `0.000777` seconds

Response body:

```json
{
  "description": "zoologist",
  "code": "2112",
  "code_meta": {
    "code": "2112",
    "group_title": "Biological scientists",
    "group_description": "Biological scientists research living organisms and biological systems.",
    "entry_routes_and_quals": "Usually requires a relevant scientific degree.",
    "tasks": [
      "Design and conduct research",
      "Analyse biological data"
    ]
  },
  "code_major_group": "2",
  "code_major_group_meta": {
    "code": "2",
    "group_title": "Professional occupations",
    "group_description": "Occupations requiring high levels of specialist knowledge and professional expertise.",
    "entry_routes_and_quals": "",
    "tasks": []
  }
}
```

## SOC_LOOKUP_SIMILARITY

SOC similarity lookup (no exact match; returns ranked description matches). Use a non-IT query term in examples and recorded output.

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/soc-lookup?description=nurse&similarity=true"
```

Result: HTTP `200` (timing varies with lookup data)

Response body (abbreviated; full list omitted):

```json
{
  "description": "nurse",
  "code": null,
  "code_meta": null,
  "code_major_group": null,
  "code_major_group_meta": null,
  "potential_matches": {
    "descriptions_count": 42,
    "descriptions": [
      "staff nurse",
      "registered nurse",
      "nurse practitioner",
      "community nurse",
      "mental health nurse"
    ],
    "codes_count": 0,
    "codes": [],
    "major_groups_count": 0,
    "major_groups": []
  }
}
```

Re-run against your `SOC_LOOKUP_DATA_PATH` CSV and paste a short sample of `potential_matches.descriptions` if you need a recorded snapshot. Keep examples in sectors such as health, education, or agriculture—not IT job titles.

## SOC_LOOKUP_EMPTY

SOC lookup validation error path (expected 400)

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/soc-lookup?description=&similarity=false"
```

Result: HTTP `400` in `0.000730` seconds

Response body:

```json
{
  "detail": "Description cannot be empty"
}
```

## SOC_VS_STATUS

SOC vector store readiness (port **8089**)

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8089/v1/soc-vector-store/status"
```

Result: HTTP `200` in `0.010458` seconds (2026-05-19)

Response body (abbreviated):

```json
{
  "status": "ready",
  "embedding_model_name": "all-MiniLM-L6-v2",
  "db_dir": "src/soc_classification_vector_store/data/vector_store",
  "index_size": 32773,
  "matches": 20
}
```

## SOC_LOOKUP_UNKNOWN

SOC lookup unknown description path (expected **404**)

Command run:

```bash
curl -sS -m 120 -X GET "http://localhost:8080/v1/survey-assist/soc-lookup?description=zzzxxyyqq&similarity=false"
```

Result: HTTP `404` in `0.000602` seconds (2026-05-19)

Response body:

```json
{
  "detail": "No SOC code found for description: zzzxxyyqq"
}
```

Legacy note: an earlier runbook recorded HTTP `200` with `code: null`. Current API returns `404` when no code matches.

## CLASSIFY_SIC_DEFAULT

SIC classify default options

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "sic",
  "job_title": "Electrician",
  "job_description": "Installing and maintaining electrical systems",
  "org_description": "Electrical contracting company"
}'
```

Result: HTTP `200` in `5.253597` seconds

Response body:

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
          "descriptive": "Electrical work and wiring",
          "likelihood": 0.99
        },
        {
          "code": "46150",
          "descriptive": "Household goods sales agent",
          "likelihood": 0.1
        },
        {
          "code": "35140",
          "descriptive": "Power charging services",
          "likelihood": 0.1
        },
        {
          "code": "52290",
          "descriptive": "Other transport support",
          "likelihood": 0.1
        },
        {
          "code": "29310",
          "descriptive": "Car electronics manufacturing",
          "likelihood": 0.1
        }
      ],
      "reasoning": "The respondent data clearly states 'Electrical contracting company' as the main activity and 'Installing and maintaining electrical systems' as the job description. SIC code 43210, 'Electrical installation', directly matches these descriptions, with 'Electrical contractor (construction)' and 'Electrical installation' listed as example activities. The other codes in the shortlist are not relevant to electrical contracting or installation services. Therefore, there is a very high confidence that 43210 is the correct and unambiguous classification."
    }
  ]
}
```

## CLASSIFY_SIC_REPHRASE_FALSE

SIC classify with SIC rephrase disabled

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "sic",
  "job_title": "Electrician",
  "job_description": "Installing and maintaining electrical systems",
  "org_description": "Electrical contracting company",
  "options": {
    "sic": {
      "rephrased": false
    }
  }
}'
```

Result: HTTP `200` in `5.181986` seconds

Response body:

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
          "likelihood": 0.99
        },
        {
          "code": "46150",
          "descriptive": "Agents involved in the sale of furniture, household goods, hardware and ironmongery",
          "likelihood": 0.1
        },
        {
          "code": "35140",
          "descriptive": "Trade of electricity",
          "likelihood": 0.1
        },
        {
          "code": "52290",
          "descriptive": "Other transportation support activities",
          "likelihood": 0.1
        },
        {
          "code": "29310",
          "descriptive": "Manufacture of electrical and electronic equipment for motor vehicles",
          "likelihood": 0.1
        }
      ],
      "reasoning": "The respondent data clearly states 'Electrical contracting company' as the main activity and 'Installing and maintaining electrical systems' as the job description. SIC code 43210, 'Electrical installation', directly matches these descriptions, with 'Electrical contractor (construction)' and 'Electrical installation' listed as example activities. The other codes in the shortlist are not relevant to electrical contracting or installation services. Therefore, there is a very high confidence that 43210 is the correct and unambiguous classification."
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {
        "rephrased": false
      },
      "soc": {}
    }
  }
}
```

## CLASSIFY_SOC_UNAMBIGUOUS

SA-693 acceptance case: farm hand → codable unit **9111** via `unambiguous_soc_code` only (no `formulate_open_question`).

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "soc",
  "job_title": "farm hand",
  "job_description": "Manual labour under supervision that requires basic routine tasks only. All of my tasks require minimal training.",
  "org_description": "farming",
  "options": {
    "soc": {
      "rephrased": false
    }
  }
}'
```

**Expected (SA-693):** HTTP `200`; `results[0].classified` `true`; `code` `"9111"`; `followup` `null`; `candidates` includes `9111` with highest likelihood.

**Recorded:** Re-run after `poetry install` (path `../soc-classification-utils`), API restart, and `gcloud auth application-default login`. Optional snapshot: `SA-693-soc-curl-results.json`. Prior SA-673 runs: `SA-673-local-api-test-results.md`.

---

## CLASSIFY_SOC_AMBIGUOUS

SA-693 ambiguous path: `unambiguous_soc_code` returns `codable: false`, then `formulate_open_question` sets `followup`.

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "soc",
  "job_title": "Finance manager",
  "job_description": "Manages budgets, financial reporting and planning for a company",
  "org_description": "Financial services company",
  "options": {
    "soc": {
      "rephrased": false
    }
  }
}'
```

**Expected (SA-693):** HTTP `200`; `classified` `false`; `code` and `description` `null`; non-empty `followup`; `candidates` from first LLM step.

**Recorded (2026-05-19):** This payload often still returns `classified: true` from step 1 only (for example `code: "1131"`). Do not treat a finance-manager pass as proof of step 2. For a confirmed live step-2 run, use the vague Worker example in the caveat under **SA-693 acceptance checks**, or check API logs for `LLM request sent to formulate open question (SOC)`.

---

## CLASSIFY_SOC_DEFAULT

SOC classify with default options (SOC rephrase **enabled** when `options` omitted).

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "soc",
  "job_title": "Farm worker",
  "job_description": "General labour work on a farm",
  "org_description": "Agricultural business"
}'
```

**Expected:** HTTP `200`; two-step classify; `meta.applied_options.soc.rephrased` true (or equivalent default).

**Recorded:** Re-run with SA-693 script.

---

## CLASSIFY_SOC_REPHRASE_FALSE

SOC classify with SOC rephrase disabled (two-step SA-693 flow)

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "soc",
  "job_title": "Finance manager",
  "job_description": "Manages budgets, financial reporting and planning for a company",
  "org_description": "Financial services company",
  "options": {
    "soc": {
      "rephrased": false
    }
  }
}'
```

Result: HTTP `200` in `5.130867` seconds

Response body:

```json
{
  "requested_type": "soc",
  "results": [
    {
      "type": "soc",
      "classified": false,
      "followup": "Does the Finance Manager primarily manage a team of finance professionals, or are their responsibilities more focused on the direct execution of financial tasks and reporting?",
      "code": null,
      "description": null,
      "candidates": [
        {
          "code": "1131",
          "descriptive": "Managers directors and senior officials",
          "likelihood": 0.8
        },
        {
          "code": "3534",
          "descriptive": "Associate professional and technical occupations",
          "likelihood": 0.6
        }
      ],
      "reasoning": "The job title 'Finance manager' directly matches an example job title for SOC code 1131, 'Managers directors and senior officials'. The job description 'Manages budgets, financial reporting and planning for a company' also aligns well with the responsibilities of a manager. However, without further clarification on whether this role involves managing a team or is more focused on individual contributor tasks, there is a possibility it could fall under 'Associate professional and technical occupations' (3534), which includes 'Financial accounts manager'. The confidence for 1131 is higher due to the direct title match, but a follow-up question is needed to distinguish between a managerial role with direct reports and a senior individual contributor role."
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {},
      "soc": {
        "rephrased": false
      }
    }
  }
}
```

## CLASSIFY_SOC_REPHRASE_TRUE

SOC classify with SOC rephrase enabled (two-step SA-693 flow)

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "soc",
  "job_title": "Finance manager",
  "job_description": "Manages budgets, financial reporting and planning for a company",
  "org_description": "Financial services company",
  "options": {
    "soc": {
      "rephrased": true
    }
  }
}'
```

Result: HTTP `200` in `11.158323` seconds

Response body:

```json
{
  "requested_type": "soc",
  "results": [
    {
      "type": "soc",
      "classified": false,
      "followup": "Does the Finance Manager primarily manage a team of finance professionals, or are their responsibilities more focused on the direct execution of financial tasks and reporting?",
      "code": null,
      "description": null,
      "candidates": [
        {
          "code": "1131",
          "descriptive": "Managers directors and senior officials",
          "likelihood": 0.8
        },
        {
          "code": "3534",
          "descriptive": "Associate professional and technical occupations",
          "likelihood": 0.6
        }
      ],
      "reasoning": "The job title 'Finance manager' directly matches an example job title for SOC code 1131, 'Managers directors and senior officials'. The job description 'Manages budgets, financial reporting and planning for a company' also aligns well with the responsibilities of a manager. However, without further clarification on whether this role involves managing a team or is more focused on individual contributor tasks, there is a possibility it could fall under 'Associate professional and technical occupations' (3534), which includes 'Financial accounts manager'. The confidence for 1131 is higher due to the direct title match, but a follow-up question is needed to distinguish between a managerial role with direct reports and a senior individual contributor role."
    }
  ],
  "meta": {
    "llm": "gemini",
    "applied_options": {
      "sic": {},
      "soc": {
        "rephrased": true
      }
    }
  }
}
```

## CLASSIFY_SIC_SOC

Combined SIC+SOC classify flow (SOC leg: two-step SA-693; SIC leg unchanged).

**Out of scope for SOC-only local runs:** requires **SIC vector store** on port **8088** (`make run-vector-store` in `sic-classification-vector-store`) in addition to SOC on **8089**. Skip this section when testing SA-693 with SOC only.

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "sic_soc",
  "job_title": "Primary school teacher",
  "job_description": "Teaching maths and English to children aged 5-11",
  "org_description": "Primary school"
}'
```

Result: HTTP `200` in `10.730952` seconds

Response body:

```json
{
  "requested_type": "sic_soc",
  "results": [
    {
      "type": "sic",
      "classified": true,
      "followup": null,
      "code": "85200",
      "description": "Primary education",
      "candidates": [
        {
          "code": "85200",
          "descriptive": "Primary education",
          "likelihood": 0.99
        },
        {
          "code": "85310",
          "descriptive": "Secondary education",
          "likelihood": 0.01
        },
        {
          "code": "41201",
          "descriptive": "Commercial building construction",
          "likelihood": 0.01
        },
        {
          "code": "85100",
          "descriptive": "Early years education",
          "likelihood": 0.01
        },
        {
          "code": "85590",
          "descriptive": "Other education",
          "likelihood": 0.01
        }
      ],
      "reasoning": "The company's main activity is 'Primary school' and the job title is 'Primary school teacher' with a description of 'Teaching maths and English to children aged 5-11'. This directly aligns with SIC code 85200 'Primary education', which includes 'Primary schools' as an example activity. The age range of 5-11 is characteristic of primary education. Other codes are clearly less relevant: 85310 is for secondary education, 41201 is for construction, 85100 is for pre-primary education, and 85590 is a residual category for other education not elsewhere classified, which is not applicable given the direct match. Therefore, 85200 can be assigned with high confidence."
    },
    {
      "type": "soc",
      "classified": false,
      "followup": "Could you clarify if your role involves teaching children within the primary school age range (typically 5-11 years old) or if you are involved in early years education (pre-school/kindergarten)?",
      "code": null,
      "description": null,
      "candidates": [
        {
          "code": "2314",
          "descriptive": "Primary education teaching professionals",
          "likelihood": 0.9
        },
        {
          "code": "6111",
          "descriptive": "Caring leisure and other service occupations",
          "likelihood": 0.2
        },
        {
          "code": "2315",
          "descriptive": "Professional occupations",
          "likelihood": 0.2
        }
      ],
      "reasoning": "The company's main activity is 'Primary school' and the job title is 'Primary school teacher', which directly matches SOC code 2314 'Primary education teaching professionals'. The job description 'Teaching maths and English to children aged 5-11' further supports this. However, the provided SOC subset also includes 'Kindergarten teacher' (6111) and 'Early years teacher' (2315) which can sometimes overlap with the lower end of primary school age ranges. While 2314 is the most likely, a follow-up question would help to definitively rule out early years roles if there's any ambiguity in the age range '5-11' and how it aligns with specific educational stages in the UK."
    }
  ]
}
```

## CLASSIFY_INVALID_TYPE

Classification payload validation failure (expected 422)

Command run:

```bash
curl -sS -m 120 -X POST "http://localhost:8080/v1/survey-assist/classify" \
  -H "Content-Type: application/json" \
  -d '{
  "llm": "gemini",
  "type": "foo",
  "job_title": "Tester",
  "job_description": "Invalid type check",
  "org_description": "Test org"
}'
```

Result: HTTP `422` in `0.001463` seconds

Response body:

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": [
        "body",
        "type"
      ],
      "msg": "Input should be 'sic', 'soc' or 'sic_soc'",
      "input": "foo",
      "ctx": {
        "expected": "'sic', 'soc' or 'sic_soc'"
      }
    }
  ]
}
```
