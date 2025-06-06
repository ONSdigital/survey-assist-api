"""Module that provides example test functions for the Survey Assist API.

Unit tests for endpoints and utility functions in the Survey Assist API.
"""

import pytest
from survey_assist_utils.logging import get_logger

from utils.survey import add_numbers

logger = get_logger(__name__)


@pytest.mark.utils
def test_add_numbers():
    """Tests the add_numbers function with various inputs."""
    assert add_numbers(1, 2) == 3  # noqa: PLR2004
    assert add_numbers(0, 0) == 0
    assert add_numbers(-1, 1) == 0
