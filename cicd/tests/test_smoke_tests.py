"""Tests for the SIC API."""

import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class TestSurveyAssistApi:
    """Test for the Survey Assist API."""

    url_base = os.environ.get("SURVEY_ASSIST_API_URL")
    if url_base is None:
        raise ValueError("SURVEY_ASSIST_API_URL environment variable is not set.")

    id_token = os.environ.get("SA_ID_TOKEN")
    if id_token is None:
        raise ValueError("SA_ID_TOKEN environment variable is not set.")

    def test_survey_assist_api_status(self) -> None:
        """Test Survey Assist API returns successful /config response."""
        endpoint = f"{self.url_base}/config"

        print(f"Calling {endpoint}...")
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {self.id_token}"},
            timeout=30,
        )

        assert (  # noqa: S101
            response.status_code == 200  # noqa: PLR2004
        ), f"Expected status code 200, but got {response.status_code}."

    def test_survey_assist_api_classify(self) -> None:
        """Test Survey Assist API returns successful /classify response."""
        retry_strategy = Retry(
            total=5,  # maximum number of retries
            backoff_factor=7,
            status_forcelist=[503],  # the HTTP status codes to retry on
        )

        # create an HTTP adapter with the retry strategy and mount it to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # create a new session object
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        endpoint = f"{self.url_base}/classify"

        print(
            f"Calling {endpoint}, will retry up to 5 times with exponential backoff.."
        )
        response = session.post(
            endpoint,
            json={
                "llm": "gemini",
                "type": "sic",
                "job_title": "Farm Hand",
                "job_description": (
                    "I work on a farm tending crops that are harvested and sold to"
                    " wholesalers"
                ),
                "org_description": (
                    "A farm that grows and harvests crops to be sold to " "wholesalers"
                ),
            },
            headers={"Authorization": f"Bearer {self.id_token}"},
            timeout=30,
        )

        assert (  # noqa: S101
            response.status_code == 200  # noqa: PLR2004
        ), f"Expected status code 200, but got {response.status_code}."
