"""Shared test helpers for SIC and SOC lookup client tests.

Used to avoid duplicate-code (e.g. pylint R0801) between test_sic_lookup_client
and test_soc_lookup_client while keeping behaviour aligned.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch


@dataclass(frozen=True)
class DataLoadingLoggingConfig:
    """Config for assert_data_loading_logging (avoids too many function args)."""

    lookup_patch_path: str
    logger_patch_path: str
    expected_count: int
    codes_substring: str
    set_get_codes_count: bool = False


def assert_data_loading_logging(
    client_class: type[Any],
    config: DataLoadingLoggingConfig,
) -> None:
    """Assert that client init logs a message containing the count and codes label.

    Both SIC and SOC lookup clients log on init (e.g. "Loaded N SIC lookup codes
    from ..."). This helper runs that init under patched lookup and logger, captures
    the log call, and asserts the message (after format) contains expected_count
    and codes_substring.
    """
    with patch(config.lookup_patch_path) as mock_lookup:
        mock_instance = mock_lookup.return_value
        mock_instance.data = MagicMock()
        mock_instance.data.__len__.return_value = config.expected_count
        if config.set_get_codes_count:
            mock_instance.get_sic_codes_count.return_value = config.expected_count

        with patch(config.logger_patch_path) as mock_logger:
            captured_message: str | None = None
            captured_args: tuple[Any, ...] | None = None

            def mock_info(message: str, *args: Any) -> None:
                nonlocal captured_message, captured_args
                captured_message = message
                captured_args = args

            mock_logger.info.side_effect = mock_info

            client_class()

            mock_logger.info.assert_called()
            assert captured_message is not None
            assert isinstance(captured_message, str)
            msg: str = captured_message
            # pylint: disable=unsupported-membership-test  # msg is str after assert above
            assert "Loaded" in msg
            assert config.codes_substring in msg
            if captured_args:
                formatted_message = msg % captured_args
                assert str(config.expected_count) in formatted_message
                assert config.codes_substring in formatted_message
            else:
                assert str(config.expected_count) in msg
                assert config.codes_substring in msg
            # pylint: enable=unsupported-membership-test
