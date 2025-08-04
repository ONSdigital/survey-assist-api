"""Utility functions for working with package data files."""

from importlib import resources
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


def resolve_package_data_path(package_name: str, filename: str) -> str:
    """Resolve the path to a data file within an installed package.

    Args:
        package_name: The package name (e.g., "industrial_classification.data")
        filename: The filename to resolve

    Returns:
        The resolved file path as a string
    """
    try:
        # Use importlib.resources to get the data file from the installed package
        data_dir = resources.files(package_name)
        resolved_path = data_dir / filename
        logger.info("Using data from installed package: %s", resolved_path)
        return str(resolved_path)
    except (ImportError, OSError) as e:
        # Fallback to hardcoded path for backward compatibility
        fallback_path = (
            f"/usr/local/lib/python3.12/site-packages/{package_name.replace('.', '/')}/"
            f"{filename}"
        )
        logger.warning(
            "Could not resolve package path, using fallback: %s. Error: %s",
            fallback_path,
            e,
        )
        return fallback_path
