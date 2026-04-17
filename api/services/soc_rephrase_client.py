"""SOC rephrase client service for the Survey Assist API.

This module provides a client for the SOC rephrase service, which maps
standard SOC descriptions to user-friendly rephrased versions.
"""

import logging
from typing import Any, Optional

import pandas as pd
from fastapi import HTTPException

from api.services.package_utils import resolve_package_data_path

logger = logging.getLogger(__name__)

# CSV column names in the SOC rephrase dataset
SOC_CODE_COL = "soc_code"
REPHRASED_DESCRIPTION_COL = "rephrased_description"
SOC_CODE_ALIASES = ("soc_code", "code", "soc")
REPHRASED_DESCRIPTION_ALIASES = (
    "rephrased_description",
    "description_rephrased",
    "rephrased",
)


class SOCRephraseClient:
    """Client for applying rephrased SOC descriptions to classification responses."""

    def __init__(self, data_path: Optional[str] = None) -> None:
        """Initialise the SOC rephrase client.

        Args:
            data_path: Optional path to the rephrased SOC dataset. When not
                provided, uses the example dataset from soc-classification-library.
        """
        source_path = self._resolve_data_path(data_path)
        self.rephrased_descriptions = self._load_rephrase_data(source_path)

        logger.info(
            "SOC rephrase data loaded from %s (%d descriptions available)",
            source_path,
            self.get_rephrased_count(),
        )

    def _resolve_data_path(self, data_path: Optional[str]) -> str:
        """Resolve and validate the SOC rephrase source path."""
        resolved = self._get_default_path() if data_path is None else data_path
        if not isinstance(resolved, str):
            raise ValueError("Data path must be a string")
        return resolved

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
            df = pd.read_csv(data_path)
            code_col = self._find_column(df, SOC_CODE_ALIASES)
            rephrased_col = self._find_column(df, REPHRASED_DESCRIPTION_ALIASES)

            rephrased_dict: dict[str, str] = {}
            for _, row in df.iterrows():
                soc_code = str(row[code_col]).strip()
                rephrased_description = str(row[rephrased_col]).strip()
                if soc_code and rephrased_description:
                    rephrased_dict[soc_code] = rephrased_description

            logger.info(
                "Loaded %d rephrased SOC descriptions from %s",
                len(rephrased_dict),
                data_path,
            )
            return rephrased_dict
        except FileNotFoundError:
            logger.error("Rephrased SOC data file not found: %s", data_path)
            raise HTTPException(
                status_code=500,
                detail=f"Rephrased SOC data file not found: {data_path}",
            ) from None
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error loading rephrased SOC data from %s: %s", data_path, exc)
            raise HTTPException(
                status_code=500,
                detail=f"Error loading rephrased SOC data: {exc}",
            ) from exc

    @staticmethod
    def _find_column(dataframe: pd.DataFrame, aliases: tuple[str, ...]) -> str:
        """Return the first matching column name from a list of aliases."""
        columns_map = {str(col).strip().lower(): str(col) for col in dataframe.columns}
        for alias in aliases:
            if alias in columns_map:
                return columns_map[alias]
        raise ValueError(f"CSV file must contain one of columns: {aliases}")

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
