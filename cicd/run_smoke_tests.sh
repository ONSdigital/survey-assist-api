#!/bin/bash

# Wrapper script to run the smoke tests locally
#
# Expected Env variables: 
# SURVEY_ASSIST_API_URL - The URL of the Survey Assist API to run the tests against
# SA_ID_TOKEN - A valid Google Identity Token generated from your credentials (assuming you're running locally) 
#

if [[ -z "${SURVEY_ASSIST_API_URL}" ]]; then
    echo Environment variable SURVEY_ASSIST_API_URL was not set, getting sandbox url from parameter store:
    SURVEY_ASSIST_API_URL=$(gcloud parametermanager parameters versions describe sandbox --parameter=infra-test-config --location=global --project ons-cicd-surveyassist --format=json | python3 -c "import sys, json; print(json.load(sys.stdin)['payload']['data'])" | base64 --decode | python3 -c "import sys, json; print(json.load(sys.stdin)['cr-api-url'])")/v1/survey-assist
    export SURVEY_ASSIST_API_URL
    echo "$SURVEY_ASSIST_API_URL"
else
    echo Using SURVEY_ASSIST_API_URL="$SURVEY_ASSIST_API_URL"
fi
#
# Example way to set token after gcloud auth login
# export SA_ID_TOKEN=`gcloud auth print-identity-token`
if [[ -z "${SA_ID_TOKEN}" ]]; then
    echo Environment variable SA_ID_TOKEN was not set, getting a new identity token from local credentials, if authenticated.
    SA_ID_TOKEN=$(gcloud auth print-identity-token)   
    export SA_ID_TOKEN 
else
    echo Using currently set SA_ID_TOKEN. If this becomes stale, run export SA_ID_TOKEN=\`gcloud auth print-identity-token\`
fi
pytest -s