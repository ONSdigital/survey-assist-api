"""SIC rephrase client service for the Survey Assist API.

This module provides a client for the SIC rephrase service, which is used to
map standard SIC descriptions to user-friendly rephrased versions.
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from survey_assist_utils.logging import get_logger

logger = get_logger(__name__)


class SICRephraseClient:
    """Client for the SIC rephrase service.

    This class provides a client for the SIC rephrase service, which is used to
    map standard SIC descriptions to user-friendly rephrased versions.

    Attributes:
        rephrase_data: Dictionary mapping SIC codes to rephrased descriptions.
    """

    def __init__(self, data_path: Optional[str] = None) -> None:
        """Initialise the SIC rephrase client.

        Args:
            data_path: Path to the SIC rephrased descriptions CSV file. If not provided,
                the default path will be used.
        """
        # Use the provided path or default path
        if data_path is None:
            resolved_path = self._get_default_path()
        else:
            resolved_path = data_path

        # Ensure the path is a string
        if isinstance(resolved_path, Path):
            resolved_path = str(resolved_path)

        # Load the rephrased descriptions data
        self.rephrase_data = self._load_rephrase_data(resolved_path)

    def _get_default_path(self) -> str:
        """Get the default path for rephrased descriptions.
        
        Priority order:
        1. Environment variable SIC_REPHRASE_DATA_PATH
        2. SIC classification library (example_rephrased_sic_data.csv)
        3. Local data directory (fallback)
        
        Returns:
            str: The default path for rephrased descriptions.
        """
        # Check environment variable first
        env_path = os.getenv("SIC_REPHRASE_DATA_PATH")
        if env_path:
            logger.info(f"Using rephrase data path from environment: {env_path}")
            return env_path

        # Try to find it in the SIC classification library
        try:
            # Look for the sic-classification-library in the parent directory
            parent_dir = Path(__file__).parent.parent.parent.parent
            sic_library_path = (
                parent_dir
                / "sic-classification-library/src/industrial_classification"
                / "data/example_rephrased_sic_data.csv"
            )
            
            if sic_library_path.exists():
                logger.info(f"Using rephrase data from SIC classification library: {sic_library_path}")
                return str(sic_library_path)
            else:
                logger.info(f"SIC classification library path not found: {sic_library_path}")
        except Exception as e:
            logger.warning(f"Could not determine SIC classification library path: {e}")

        # Fallback to local data directory
        project_root = Path(__file__).parent.parent.parent
        local_path = project_root / "data" / "sic_rephrased_descriptions.csv"
        logger.info(f"Using local rephrase data path: {local_path}")
        return str(local_path)

    def _load_rephrase_data(self, data_path: str) -> Dict[str, str]:
        """Load rephrased descriptions from CSV file.

        Args:
            data_path: Path to the CSV file containing rephrased descriptions.

        Returns:
            Dictionary mapping SIC codes to rephrased descriptions.
        """
        try:
            # Load CSV with SIC codes as strings to handle leading zeros
            df = pd.read_csv(data_path, dtype={"sic_code": str})
            
            # Check if this is the new format (from sic-classification-library)
            if "reviewed_description" in df.columns:
                # Use the reviewed_description column from the existing file
                rephrase_dict = df.set_index("sic_code")["reviewed_description"].to_dict()
                logger.info(f"Loaded {len(rephrase_dict)} rephrased SIC descriptions from {data_path} (reviewed_description format)")
            elif "reviewed_description" in df.columns:
                # Fallback to the original format
                rephrase_dict = df.set_index("sic_code")["reviewed_description"].to_dict()
                logger.info(f"Loaded {len(rephrase_dict)} rephrased SIC descriptions from {data_path} (original format)")
            else:
                logger.warning(f"CSV file {data_path} does not contain expected columns. Available columns: {list(df.columns)}")
                return {}
            
            return rephrase_dict
            
        except FileNotFoundError:
            logger.warning(f"Rephrased descriptions file not found at {data_path}. Using empty mapping.")
            return {}
        except Exception as e:
            logger.error(f"Error loading rephrased descriptions from {data_path}: {e}")
            return {}

    def get_rephrased_description(self, sic_code: str) -> Optional[str]:
        """Get the rephrased description for a given SIC code.

        Args:
            sic_code: The SIC code to look up.

        Returns:
            The rephrased description if found, None otherwise.
        """
        # Ensure SIC code is a string and handle leading zeros
        sic_code_str = str(sic_code).zfill(5)
        return self.rephrase_data.get(sic_code_str)

    def process_classification_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a classification response to include rephrased descriptions.

        Args:
            response_data: The classification response data.

        Returns:
            The response data with rephrased descriptions added.
        """
        # Process main SIC description
        if response_data.get("sic_code"):
            rephrased_desc = self.get_rephrased_description(response_data["sic_code"])
            if rephrased_desc:
                response_data["sic_description"] = rephrased_desc
                logger.debug(f"Rephrased main SIC description for code {response_data['sic_code']}")

        # Process SIC candidates
        for candidate in response_data.get("sic_candidates", []):
            if candidate.get("sic_code"):
                rephrased_desc = self.get_rephrased_description(candidate["sic_code"])
                if rephrased_desc:
                    candidate["sic_descriptive"] = rephrased_desc
                    logger.debug(f"Rephrased candidate description for code {candidate['sic_code']}")

        return response_data

    def get_rephrased_count(self) -> int:
        """Get the total number of rephrased descriptions available.

        Returns:
            int: The total number of rephrased descriptions available.
        """
        return len(self.rephrase_data) 