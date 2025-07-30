"""This module contains pytest configuration and hooks.

It sets up a global logger and defines hooks for pytest to log events
such as the start and finish of a test session.

Functions:
    pytest_configure(config): Applies global test configuration.
    pytest_sessionstart(session): Logs the start of a test session.
    pytest_sessionfinish(session, exitstatus): Logs the end of a test session.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from industrial_classification_utils.llm.llm import ClassificationLLM
from survey_assist_utils.logging import get_logger

from api.main import app
from api.routes.v1.sic_lookup import get_lookup_client
from api.services.sic_lookup_client import SICLookupClient

# Configure a global logger
logger = get_logger(__name__)


def pytest_configure(config):  # pylint: disable=unused-argument
    """Hook function for pytest that is called after command line options have been parsed
    and all plugins and initial configuration are set up.

    This function is typically used to perform global test configuration or setup
    tasks before any tests are executed.

    Args:
        config (pytest.Config): The pytest configuration object containing command-line
            options and plugin configurations.
    """
    # Mock the LLM initialisation
    mock_llm = MagicMock(spec=ClassificationLLM)
    mock_llm.model_name = "gemini-1.5-flash"  # Set the model name for config endpoint

    # Mock the sa_rag_sic_code method to return expected values
    mock_llm.sa_rag_sic_code.return_value = (
        MagicMock(
            classified=True,
            codable=True,
            followup=None,
            sic_code="43210",
            sic_descriptive="Electrical installation",
            reasoning="Mocked reasoning",
            sic_candidates=[
                MagicMock(
                    sic_code="43210",
                    sic_descriptive="Electrical installation",
                    likelihood=0.95,
                )
            ],
        ),
        None,
        None,
    )

    app.state.gemini_llm = mock_llm
    logger.info("Global Test Configuration Applied")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):  # pylint: disable=unused-argument
    """Pytest hook implementation that is executed at the start of a test session.

    This function logs a message indicating that the test session has started.

    Args:
        session: The pytest session object (not used in this implementation).
    """
    logger.info("Test Session Started")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):  # pylint: disable=unused-argument
    """Pytest hook implementation that is executed at the end of a test session.

    This function logs a message indicating that the test session has finished,
    including the exit status of the session.

    Args:
        session: The pytest session object (not used in this implementation).
        exitstatus: The exit status of the test session.
    """
    logger.info(f"Test Session Finished with Status: {exitstatus}")


# Get the absolute path to the test data file
TEST_DATA_PATH = str(Path(__file__).parent / "data" / "example_sic_lookup_data.csv")


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app.

    Returns:
        TestClient: A test client for the FastAPI app.
    """
    # Override the SIC lookup client to use test data
    app.dependency_overrides[get_lookup_client] = lambda: SICLookupClient(
        data_path=TEST_DATA_PATH
    )
    return TestClient(app)
