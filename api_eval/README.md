# WIP - API Evaluation

The functionality here is a first attempt at evaluating results from the LLM for SIC classify requests. It is a work in progress and a supporting tool (not part of production build).

## High-level Overview

The script comprises the following source code:

### classify_body.py - CSV Row Loading and Classify Request Formatting

This module is responsible for converting rows from a CSV dataset into valid request bodies for the /classify API endpoint. It allows large batches of test inputs to be executed consistently by combining structured CSV input data with a JSON request template.

The workflow consists of two main steps:

#### Load test rows from a CSV file

```load_rows()``` reads a CSV file using pandas and converts each row into a dictionary.

The loader:

- Treats all values as strings to avoid type conversion issues

- Strips whitespace from column names and values

- Logs bad rows instead of failing

Each CSV row becomes a dictionary that can be used to populate a request template.

#### Render API request bodies from a JSON template using those rows

```render_body_from_template()``` fills a JSON template using values from a CSV row.
It replaces ${...} placeholders with the corresponding row values and returns a dictionary ready to send to the /classify endpoint.

The function also ensures required request fields such as llm and type are set.

**Classify Template Example**

The request template uses string.Template placeholders that are replaced with CSV values:

```json
{
    "llm": "gemini",
    "type": "sic",
    "job_title": ${job_title_column},
    "job_description": ${job_description_column},
    "org_description": ${org_description_column}
}
```

This approach allows the API test harness to separate test data (CSV) from request structure (JSON template), making it easier to maintain, extend, and reuse tests.

This allows a single CSV row with:

- job_title: Nurse
- job_description: Care for people
- org_description: Providing people with treatment

Will be correctly formatted as a ```POST``` request to the ```/classify``` endpoint

### classify_validators.py - Classify Response Validation

This module validates ```/classify``` API responses against expected values derived from the CSV test data. It applies a set of rules that compare expected values from the input row with actual values returned by the API.

The functionality comprises two main steps:

#### Define Validation Rules

Validation rules describe how a CSV row and an API response should be compared. Each rule specifies:

- how to derive the expected value from the CSV row

- how to extract the actual value from the API response

- how the two values should be compared

Rules are represented using the ```Rule``` dataclass.

#### Run Validation

```validate_row()``` applies all defined rules to a CSV row and its corresponding API response.

The function returns:

- Validation failures – rules that did not match

- Validation warnings – rules that passed but produced a caution (for example candidate ordering differences)

This allows the test harness to distinguish between critical errors and informational issues.

#### Rule Types

Simple rules compare one expected value to one value in the response.

**Rules**

```classified.value``` - Ensures ```response.results[0].classified``` matches the expected classification outcome

```code.value``` - Ensures the returned SIC code matches the expected assigned code

```candidate_codes.count``` - Ensures the number of returned candidate codes matches the CSV

**Compound Rules (```CompoundRule```)**

Compound rules perform more complex validation that may produce both failures and warnings.

```alt_candidate.codes_match``` - Ensures the candidate code set returned by the API matches the input CSV

This rule:

**Fails** if expected candidate codes are missing or unexpected codes appear

**Warns** if the codes match but appear in a different order

### run_classify.py - API Evaluation Runner

This script runs the full API evaluation workflow by sending requests to the ```/classify``` endpoint and validating the responses against expected values derived from the CSV dataset.

It combines three components:

- CSV input data (test case, taking the eval CSV format produced in public testing)
- JSON request template (request structure)
- validation rules (response checks)

The main parts of the workflow are:

#### Load Test Data and Build Requests

The script reads rows from a CSV file and renders a request body for each row using the JSON template.

Each request is sent to the configured ```/classify API``` endpoint using httpx.

#### Send Requests to the API

For each row:

1. The request body is generated from the template.
2. A POST request is sent to the API endpoint.
3. The JSON response is parsed and validated.

If the API returns a non-200 response or invalid JSON, the row is marked as a failure.

#### Validate the Response

Each successful response is validated using the configured rules.

- classified.value
- code.value
- candidate_codes.count
- alt_candidate.codes_match

These rules compare the API response against expected values derived from the CSV input.

#### Save Results (Optional)

If ```--save-responses``` is enabled, the script writes results to a JSONL output file.

Each record includes:

- request metadata
- API response
- validation results
- pass/fail status

A final run summary is appended containing:

- total rows tested
- passed vs failed rows
- failed row IDs
- counts of key rule failures

## Running the Evaluation

Example command:

```bash
poetry run python -m api_eval.run_classify \
--csv data/results.csv \
--template scripts/artifacts/ template_classify_body.json \
--save-responses \
--out-dir scripts/output \
--run-id local_test_run
```

```--csv``` - the example input CSV (this uses the eval format from public testing)
```--template``` - the classify body template (example in README)
```--save-responses``` - will generate a jsonl file containing per row test output
```--out-dir``` - the directory to write output to
```--run-id``` - a descriptor to store against results


## Results

Summary results are output at the CLI.

E.g:
```
Run summary: 60 rows — 41 passed, 19 failed,3 classified value failures

--- Failed rows ---
0w03uGgpO1D8ggi5CRWH
16tpLsq2MTaIPeonhmwc
CQz5pr7P5TdQWnBaAkNX
DsCmVIfHwzFIWzpgC2uJ
EKJ926vlQv7Eb3zf7lBU
FFrw4RQXX7ov9nAt5yER
Fvy1rFtAXV03KppMRjfk
KcKFhgceXk16PcYYPW03
PZ0iVS2HjyrEQUnIURWt
QaJOwPI2wSuhXeGPIbGc
SFWDoeLjurthb6XJqGyJ
cWxJZC0CfDjLvkA8hRIM
gJyQxjq9TTWAVjeJdC0F
rAizD8cPu39O0Q9vb6Vt
rQZXdNoCeIr0hgtY8IFJ
ww5fi6HypotJ1JZu2NAK
yL9ETWAmluXJwn4EEzH7
zFGr3PPjuYx7ryfwUNX7
zxCbFkwgvUTo8IWlqXdV

--- Failure details ---
0w03uGgpO1D8ggi5CRWH: candidate_codes.count failed. expected=5 actual=2
0w03uGgpO1D8ggi5CRWH: alt_candidate.codes_match_set failed. expected=['43910', '84230', '08910', '71121', '55100'] actual=['43910', '43320']
16tpLsq2MTaIPeonhmwc: alt_candidate.codes_match_set failed. expected=['81210', '46439', '46900', '46499', '52103'] actual=['81210', '78200', '41201', '28940', '18130']
CQz5pr7P5TdQWnBaAkNX: alt_candidate.codes_match_set failed. expected=['90010', '90030', '90020', '94120', '60200'] actual=['90010', '90020', '90030', '94120', '13100']
DsCmVIfHwzFIWzpgC2uJ: HTTP 400: {'detail': 'Job title and description cannot be empty'}
EKJ926vlQv7Eb3zf7lBU: candidate_codes.count failed. expected=3 actual=4
EKJ926vlQv7Eb3zf7lBU: alt_candidate.codes_match_set failed. expected=['84110', '63110', '62020'] actual=['84110', '63110', '94120', '62020']
FFrw4RQXX7ov9nAt5yER: candidate_codes.count failed. expected=5 actual=3
FFrw4RQXX7ov9nAt5yER: alt_candidate.codes_match_set failed. expected=['84110', '84240', '84230', '94910', '85320'] actual=['84110', '84240', '84230']
Fvy1rFtAXV03KppMRjfk: candidate_codes.count failed. expected=3 actual=5
Fvy1rFtAXV03KppMRjfk: alt_candidate.codes_match_set failed. expected=['71129', '70229', '62012'] actual=['84110', '71129', '70229', '62012', '16230']
KcKFhgceXk16PcYYPW03: classified.value failed. expected=True actual=False
KcKFhgceXk16PcYYPW03: code.value failed. expected='93210' actual=None
KcKFhgceXk16PcYYPW03: alt_candidate.codes_match_set failed. expected=['93210', '90010', '92000', '46499', '82301'] actual=['32990', '94990', '90010', '92000', '46499']
PZ0iVS2HjyrEQUnIURWt: candidate_codes.count failed. expected=4 actual=5
PZ0iVS2HjyrEQUnIURWt: alt_candidate.codes_match_set failed. expected=['84120', '86101', '87200', '86220'] actual=['84120', '86101', '87200', '86220', '94120']
QaJOwPI2wSuhXeGPIbGc: candidate_codes.count failed. expected=5 actual=3
QaJOwPI2wSuhXeGPIbGc: alt_candidate.codes_match_set failed. expected=['28410', '71121', '30200', '45200', '49410'] actual=['29100', '28410', '45200']
SFWDoeLjurthb6XJqGyJ: alt_candidate.codes_match_set failed. expected=['70229', '71129', '71111', '56302', '69201'] actual=['70229', '71129', '56302', '71111', '64209']
cWxJZC0CfDjLvkA8hRIM: classified.value failed. expected=True actual=False
cWxJZC0CfDjLvkA8hRIM: code.value failed. expected='17219' actual=None
gJyQxjq9TTWAVjeJdC0F: alt_candidate.codes_match_set failed. expected=['58190', '84110', '94120', '26513', '26511'] actual=['58190', '84110', '94120', '01130', '26513']
rAizD8cPu39O0Q9vb6Vt: candidate_codes.count failed. expected=5 actual=4
rAizD8cPu39O0Q9vb6Vt: alt_candidate.codes_match_set failed. expected=['49390', '49319', '52290', '49100', '79110'] actual=['49390', '49319', '52290', '49100']
rQZXdNoCeIr0hgtY8IFJ: candidate_codes.count failed. expected=3 actual=5
rQZXdNoCeIr0hgtY8IFJ: alt_candidate.codes_match_set failed. expected=['56301', '56302', '85520'] actual=['56301', '94990', '93130', '93120', '85520']
ww5fi6HypotJ1JZu2NAK: candidate_codes.count failed. expected=3 actual=5
ww5fi6HypotJ1JZu2NAK: alt_candidate.codes_match_set failed. expected=['85200', '85310', '85100'] actual=['85200', '85310', '85100', '85590', '85600']
yL9ETWAmluXJwn4EEzH7: alt_candidate.codes_match_set failed. expected=['81210', '81299', '96010', '46440', '47789'] actual=['81210', '81299', '96010', '46440', '70100']
zFGr3PPjuYx7ryfwUNX7: alt_candidate.codes_match_set failed. expected=['77299', '46150', '47110', '47599', '46499'] actual=['77299', '46150', '47110', '47599', '70100']
zxCbFkwgvUTo8IWlqXdV: classified.value failed. expected=True actual=False
zxCbFkwgvUTo8IWlqXdV: code.value failed. expected='94910' actual=None
```

The jsonl file generated with ```--save-responses``` gives processabe output.
