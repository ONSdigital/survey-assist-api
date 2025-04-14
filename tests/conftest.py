"""This module contains pytest configuration and hooks.

It sets up a global logger and defines hooks for pytest to log events
such as the start and finish of a test session.

Functions:
    pytest_configure(config): Applies global test configuration.
    pytest_sessionstart(session): Logs the start of a test session.
    pytest_sessionfinish(session, exitstatus): Logs the end of a test session.
"""

import logging
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

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
    """Hook function called after the test session ends.

    This function is executed after all tests have been run and the test session
    is about to finish. It can be used to perform cleanup or logging tasks.

    Args:
        session (Session): The pytest session object containing information
            about the test session.
        exitstatus (int): The exit status code of the test session. This indicates
            whether the tests passed, failed, or were interrupted.

    Note:
        The `pylint: disable=unused-argument` directive is used to suppress
        warnings for unused arguments in this function.
    """
    logger.info("=== Test Session Finished ===")


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data files.

    Returns:
        Path: Path to the test data directory.
    """
    test_dir = Path(__file__).parent
    data_dir = test_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def sic_data_file(test_data_dir):
    """Create a test SIC data file.

    Args:
        test_data_dir (Path): Path to the test data directory.

    Returns:
        Path: Path to the test SIC data file.
    """
    data_file = test_data_dir / "sic_codes.csv"

    # Create a minimal SIC data file
    with open(data_file, "w", encoding="utf-8") as f:
        f.write("code,description\n")
        f.write(
            "01110,Growing of cereals (except rice), leguminous crops and oil seeds\n"
        )
        f.write("01120,Growing of rice\n")
        f.write("01130,Growing of vegetables and melons, roots and tubers\n")

    return data_file


@pytest.fixture(scope="session")
def has_sic_data():
    """Check if the SIC data file exists.

    Returns:
        bool: True if the SIC data file exists, False otherwise.
    """
    default_path = Path(
        "../sic-classification-library/src/industrial_classification/data/sic_knowledge_base_utf8.csv"
    )
    return default_path.exists()


@pytest.fixture(scope="session")
def client(sic_data_file, has_sic_data):
    """Create a test client for the FastAPI app.

    Args:
        sic_data_file (Path): Path to the test SIC data file.
        has_sic_data (bool): Whether the SIC data file exists.

    Returns:
        TestClient: A test client for the FastAPI app.
    """
    # Set the environment variable for the test data file
    os.environ["SIC_DATA_FILE"] = str(sic_data_file)

    return TestClient(app)
