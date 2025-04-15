"""This module contains pytest configuration and hooks.

It sets up a global logger and defines hooks for pytest to log events
such as the start and finish of a test session.

Functions:
    pytest_configure(config): Applies global test configuration.
    pytest_sessionstart(session): Logs the start of a test session.
    pytest_sessionfinish(session, exitstatus): Logs the end of a test session.
"""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.v1.sic_lookup import get_lookup_client
from api.services.sic_lookup_client import SICLookupClient

# Configure a global logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Adjust level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
)


def pytest_configure(config):  # pylint: disable=unused-argument
    """Hook function for pytest that is called after command line options have been parsed
    and all plugins and initial configuration are set up.

    This function is typically used to perform global test configuration or setup
    tasks before any tests are executed.

    Args:
        config (pytest.Config): The pytest configuration object containing command-line
            options and plugin configurations.
    """
    logger.info("=== Global Test Configuration Applied ===")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):  # pylint: disable=unused-argument
    """Pytest hook implementation that is executed at the start of a test session.

    This function logs a message indicating that the test session has started.

    Args:
        session: The pytest session object (not used in this implementation).
    """
    logger.info("=== Test Session Started ===")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):  # pylint: disable=unused-argument
    """Pytest hook implementation that is executed at the end of a test session.

    This function logs a message indicating that the test session has finished,
    including the exit status of the session.

    Args:
        session: The pytest session object (not used in this implementation).
        exitstatus: The exit status of the test session.
    """
    logger.info("=== Test Session Finished with Status: %s ===", exitstatus)


@pytest.fixture(scope="session")
def test_data_directory():
    """Return the path to the test data directory.

    Returns:
        Path: Path to the test data directory.
    """
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sic_test_data_file(test_data_dir_path):
    """Return the path to the test SIC data file.

    Args:
        test_data_dir_path (Path): Path to the test data directory.

    Returns:
        Path: Path to the test SIC data file.
    """
    return test_data_dir_path / "example_sic_lookup_data.csv"


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app.

    Returns:
        TestClient: A test client for the FastAPI app.
    """

    # Override the get_lookup_client function to use the test data
    def get_test_lookup_client() -> SICLookupClient:
        return SICLookupClient(data_path="tests/data/example_sic_lookup_data.csv")

    app.dependency_overrides[get_lookup_client] = get_test_lookup_client

    return TestClient(app)
