"""SIC rephrase client service for the Survey Assist API.

This module provides a client for the SIC rephrase service, which is used to
map standard SIC descriptions to user-friendly rephrased versions.
"""

import importlib.util
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)

# Constants
FOUR_DIGIT_SIC_CODE = 4


class SICRephraseClient:
    """Client for applying rephrased SIC descriptions to classification responses."""

    def __init__(self, data_path: Optional[str] = None):
        """Initialise the SIC rephrase client.

        Args:
            data_path (Optional[str]): Path to the rephrased SIC data file.
                If None, uses default path from SIC classification library.
        """
        # Use the provided path or default path
        resolved_path = self._get_default_path() if data_path is None else data_path

        # Ensure the path is a string
        if not isinstance(resolved_path, str):
            raise ValueError("Data path must be a string")

        # Load the rephrased descriptions
        self.rephrased_descriptions = self._load_rephrase_data(resolved_path)

    def _get_default_path(self) -> str:
        """Get the default path to the rephrased SIC data file.

        Returns:
            str: Path to the rephrased SIC data file.
        """
        # Check for environment variable first
        env_path = os.environ.get("SIC_REPHRASE_DATA_PATH")
        if env_path:
            logger.info(f"Using rephrase data from environment variable: {env_path}")
            return env_path

        # Use the SIC classification library path
        try:
            # Just check if the module exists, we don't need to import the class
            if importlib.util.find_spec("industrial_classification.lookup.sic_lookup"):
                # Get the path from the SIC classification library
                base_path = Path(__file__).parent.parent.parent
                data_file = (
                    "sic-classification-library/src/industrial_classification/data/"
                    "example_rephrased_sic_data.csv"
                )
                local_path = base_path / data_file
                logger.info(
                    f"Using rephrase data from SIC classification library: {local_path}"
                )
                return str(local_path)
            raise ImportError("Module not found")
        except ImportError:
            # Fallback to local path if SIC classification library is not available
            local_path = Path(__file__).parent / "data/example_rephrased_sic_data.csv"
            logger.info(f"Using rephrase data from local path: {local_path}")
            return str(local_path)

    def _load_rephrase_data(self, data_path: str) -> dict[str, str]:
        """Load rephrased descriptions from CSV file.

        Args:
            data_path (str): Path to the CSV file containing rephrased descriptions.

        Returns:
            dict[str, str]: Dictionary mapping SIC codes to rephrased descriptions.

        Raises:
            HTTPException: If the data file cannot be loaded.
        """
        try:
            # Read the CSV file with explicit dtype for sic_code to ensure it's treated as string
            df = pd.read_csv(data_path, dtype={"sic_code": str})

            # Validate required columns
            required_columns = ["sic_code", "reviewed_description"]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV file must contain columns: {required_columns}")

            # Create dictionary mapping SIC codes to rephrased descriptions
            rephrased_dict = {}
            for _, row in df.iterrows():
                sic_code = str(row["sic_code"]).strip()
                reviewed_description = str(row["reviewed_description"]).strip()

                if sic_code and reviewed_description:
                    rephrased_dict[sic_code] = reviewed_description

            logger.info(
                f"Loaded {len(rephrased_dict)} rephrased SIC descriptions from {data_path} "
                f"(reviewed_description format)"
            )
            return rephrased_dict

        except FileNotFoundError:
            logger.error(f"Rephrased SIC data file not found: {data_path}")
            raise HTTPException(
                status_code=500,
                detail=f"Rephrased SIC data file not found: {data_path}",
            ) from None
        except Exception as e:
            logger.error(f"Error loading rephrased SIC data from {data_path}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error loading rephrased SIC data: {e}"
            ) from e

    def get_rephrased_description(self, sic_code: str) -> Optional[str]:
        """Get the rephrased description for a given SIC code.

        Args:
            sic_code (str): The SIC code to look up.

        Returns:
            Optional[str]: The rephrased description if available, None otherwise.
        """
        sic_code = str(sic_code).strip()

        # Try exact match first
        if sic_code in self.rephrased_descriptions:
            return self.rephrased_descriptions[sic_code]

        # Follow the same logic as SIC lookup: pad 4-digit codes to 5 digits
        if len(sic_code) == FOUR_DIGIT_SIC_CODE:
            sic_code_padded = f"0{sic_code}"
            if sic_code_padded in self.rephrased_descriptions:
                return self.rephrased_descriptions[sic_code_padded]

        return None

    def get_rephrased_count(self) -> int:
        """Get the number of available rephrased descriptions.

        Returns:
            int: Number of rephrased descriptions loaded.
        """
        return len(self.rephrased_descriptions)

    def has_rephrased_description(self, sic_code: str) -> bool:
        """Check if a rephrased description exists for a given SIC code.

        Args:
            sic_code (str): The SIC code to check.

        Returns:
            bool: True if a rephrased description exists, False otherwise.
        """
        return str(sic_code).strip() in self.rephrased_descriptions

    def process_classification_response(
        self, response_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a classification response to include rephrased descriptions.

        Args:
            response_data (dict[str, Any]): The classification response data.

        Returns:
            dict[str, Any]: The processed response data with rephrased descriptions.
        """
        # Create a copy to avoid modifying the original
        processed_response = response_data.copy()

        # Apply rephrased description to the main SIC code if available
        if processed_response.get("sic_code"):
            sic_code = str(processed_response["sic_code"])
            rephrased_desc = self.get_rephrased_description(sic_code)
            if rephrased_desc:
                processed_response["sic_description"] = rephrased_desc

        # Apply rephrased descriptions to candidates if available
        if processed_response.get("sic_candidates"):
            for candidate in processed_response["sic_candidates"]:
                if candidate.get("sic_code"):
                    sic_code = str(candidate["sic_code"])
                    rephrased_desc = self.get_rephrased_description(sic_code)
                    if rephrased_desc:
                        candidate["sic_descriptive"] = rephrased_desc

        return processed_response
