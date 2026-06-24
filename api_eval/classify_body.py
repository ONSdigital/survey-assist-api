# Parse CSV rows and render request bodies for /classify from templates.
#
from __future__ import annotations

import csv
import json
from pathlib import Path
from string import Template
from typing import Any, Dict

import pandas as pd


def load_rows(csv_path: str | Path) -> list[dict[str, Any]]:
    df = pd.read_csv(
        csv_path,
        sep=",",
        engine="python",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,  # standard CSV quoting
        skipinitialspace=True,  # helps with " , value" style spacing
        dtype=str,  # prevent pandas turning codes into floats/NaN
        keep_default_na=False,  # keep empty as "" instead of NaN
        on_bad_lines="warn",  # log bad lines instead of failing
    )

    # normalize column names (you had trailing spaces before)
    df.columns = [str(c).strip() for c in df.columns]

    # also strip whitespace in string cells (optional but usually helpful)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    return df.to_dict(orient="records")


def render_body_from_template(
    template_path: str | Path,
    row: dict[str, Any],
    *,
    job_title_key: str = "job_title",
    job_description_key: str = "job_description",
    org_description_key: str = "org_description",
    llm: str = "gemini",
    request_type: str = "sic",
) -> Dict[str, Any]:
    """Renders a JSON template (string.Template style placeholders like ${job_title_column})
    into a concrete request body for a CSV row.
    """
    template_text = Path(template_path).read_text(encoding="utf-8")
    payload_text = Template(template_text).safe_substitute(
        job_title_column=str(row.get(job_title_key, "") or ""),
        job_description_column=str(row.get(job_description_key, "") or ""),
        org_description_column=str(row.get(org_description_key, "") or ""),
    )
    body = json.loads(payload_text)
    # Ensure fixed fields are present/consistent
    body["llm"] = llm
    body["type"] = request_type
    return body
