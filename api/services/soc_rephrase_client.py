"""SOC rephrase client for the Survey Assist API.

This client mirrors the behaviour of the SIC rephrase client, but for SOC:
it loads a packaged SOC rephrase dataset and provides helpers to look up
respondent-friendly descriptions by `soc_code` and to post-process SOC
classification responses.
"""

from typing import Any, Optional

import pandas as pd
from fastapi import HTTPException
from survey_assist_utils.logging import get_logger

from api.services.package_utils import resolve_package_data_path

logger = get_logger(__name__)

# CSV column names in the SOC rephrase dataset
SOC_CODE_COL = "soc_code"
REPHRASED_DESCRIPTION_COL = "rephrased_description"


class SOCRephraseClient:
    """Client for applying rephrased SOC descriptions to classification responses."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        """Initialise the SOC rephrase client.

        Args:
            data_path: Optional path to the rephrased SOC dataset. When not
                provided, uses the example dataset from soc-classification-library.
        """
        resolved_path: Any = (
            self._get_default_path() if data_path is None else data_path
        )
        if not isinstance(resolved_path, str):
            raise ValueError("Data path must be a string")

        self.rephrased_descriptions = self._load_rephrase_data(resolved_path)

        logger.info(
            "SOC rephrase client initialised",
            data_path=resolved_path,
            rephrased_count=str(self.get_rephrased_count()),
        )

    def _get_default_path(self) -> str:
        """Get the default path to the rephrased SOC data file."""
        return resolve_package_data_path(
            "occupational_classification.data",
            "example_rephrased_soc_data.csv",
        )

    def _load_rephrase_data(self, data_path: str) -> dict[str, str]:
        """Load rephrased SOC descriptions from CSV file.

        Args:
            data_path: Path to the CSV file containing rephrased descriptions.

        Returns:
            Dictionary mapping SOC codes to rephrased descriptions.

        Raises:
            HTTPException: If the file is not found or has invalid format.
        """
        try:
            df = pd.read_csv(data_path, dtype={SOC_CODE_COL: str})

            required_columns = [SOC_CODE_COL, REPHRASED_DESCRIPTION_COL]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"CSV file must contain columns: {required_columns}")

            rephrased_dict: dict[str, str] = {}
            for _, row in df.iterrows():
                soc_code = str(row[SOC_CODE_COL]).strip()
                rephrased_description = str(row[REPHRASED_DESCRIPTION_COL]).strip()
                if soc_code and rephrased_description:
                    rephrased_dict[soc_code] = rephrased_description

            logger.info(
                "Loaded rephrased SOC descriptions",
                rephrased_count=str(len(rephrased_dict)),
                data_path=data_path,
            )
            return rephrased_dict
        except FileNotFoundError:
            logger.error(
                "Rephrased SOC data file not found",
                data_path=data_path,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Rephrased SOC data file not found: {data_path}",
            ) from None
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "Error loading rephrased SOC data",
                data_path=data_path,
                error=str(exc),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Error loading rephrased SOC data: {exc}",
            ) from exc

    def get_rephrased_description(self, soc_code: str) -> Optional[str]:
        """Get the rephrased description for a given SOC code, if available."""
        code = str(soc_code).strip()
        if not code:
            return None
        return self.rephrased_descriptions.get(code)

    def get_rephrased_count(self) -> int:
        """Return the number of available rephrased SOC descriptions."""
        return len(self.rephrased_descriptions)

    def has_rephrased_description(self, soc_code: str) -> bool:
        """Return True if a rephrased description exists for the given SOC code."""
        return self.get_rephrased_description(soc_code) is not None

    def process_classification_response(
        self, response_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a SOC classification response to include rephrased descriptions.

        Mirrors the SIC rephrase client behaviour, but for SOC fields:
        soc_code, soc_description, soc_candidates, soc_descriptive.
        """
        processed_response = response_data.copy()

        # Rephrase main SOC description if a code is present
        if processed_response.get("soc_code"):
            soc_code = str(processed_response["soc_code"])
            rephrased_desc = self.get_rephrased_description(soc_code)
            if rephrased_desc:
                processed_response["soc_description"] = rephrased_desc

        # Rephrase SOC candidates if present
        if processed_response.get("soc_candidates"):
            for candidate in processed_response["soc_candidates"]:
                if candidate.get("soc_code"):
                    soc_code = str(candidate["soc_code"])
                    rephrased_desc = self.get_rephrased_description(soc_code)
                    if rephrased_desc:
                        candidate["soc_descriptive"] = rephrased_desc

        return processed_response
