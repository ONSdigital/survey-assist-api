"""Module that provides example test functions for the Survey Assist API.

Unit tests for endpoints and utility functions in the Survey Assist API.
"""

import pytest
from survey_assist_utils.logging import get_logger

from utils.survey import truncate_identifier

logger = get_logger(__name__)


@pytest.mark.utils
def test_truncate_identifier():
    """Tests the truncate_identifier function with various inputs."""
    assert truncate_identifier("short", 10) == "short"
    assert truncate_identifier("very long string here", 10) == "very long ..."
    assert truncate_identifier(None, 10) == ""
    assert truncate_identifier("", 10) == ""
    assert truncate_identifier("exact", 5) == "exact"
