"""Module that provides example test functions for the Survey Assist API.

Unit tests for endpoints and utility functions in the Survey Assist API.
"""

import logging

import pytest

from utils.survey import add_numbers

logger = logging.getLogger(__name__)


@pytest.mark.utils
def test_add_numbers():
    """Tests the add_numbers function with various inputs."""
    assert add_numbers(1, 2) == 3  # noqa: PLR2004
    assert add_numbers(0, 0) == 0
    assert add_numbers(-1, 1) == 0
