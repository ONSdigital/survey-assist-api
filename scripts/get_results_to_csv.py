#!/usr/bin/env python3
"""Fetch survey-assist results for a wave_id + survey_id, flatten to rows, and optionally write CSV."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from typing import Any

import requests


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _safe_get(d: Any, *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _pick_first_response(obj: dict[str, Any]) -> dict[str, Any]:
    responses = _as_list(obj.get("responses"))
    if responses and isinstance(responses[0], dict):
        return responses[0]
    return {}


def _inputs_to_map(interaction: dict[str, Any]) -> dict[str, Any]:
    """Convert interaction.input = [{"field": "...", "value": "..."}] to {"job_title": "...", ...}"""
    out: dict[str, Any] = {}
    for item in _as_list(interaction.get("input")):
        if isinstance(item, dict):
            field = item.get("field")
            if field:
                out[str(field)] = item.get("value")
    return out


def _normalize_job_desc_key(inputs_map: dict[str, Any]) -> Any:
    # Some places call it job_desc; your examples show job_description.
    return inputs_map.get("job_description", inputs_map.get("job_desc"))


def _find_interaction(
    interactions: list[dict[str, Any]], interaction_type: str
) -> dict[str, Any] | None:
    for it in interactions:
        if isinstance(it, dict) and it.get("type") == interaction_type:
            return it
    return None


def _extract_followup_questions(
    classify_interaction: dict[str, Any],
) -> list[dict[str, Any]]:
    questions = _safe_get(
        classify_interaction, "response", "follow_up", "questions", default=[]
    )
    return [q for q in _as_list(questions) if isinstance(q, dict)]


def _get_question(questions: list[dict[str, Any]], idx: int) -> dict[str, Any] | None:
    if 0 <= idx < len(questions):
        return questions[idx]
    return None


def _pad_list(values: list[Any], length: int, pad: Any = "") -> list[Any]:
    values = list(values)
    if len(values) >= length:
        return values[:length]
    return values + [pad] * (length - len(values))


@dataclass
class FlattenedRow:
    unique_id: str
    user: str
    job_title: str
    job_description: str
    org_description: str

    survey_assist_open_question: str
    survey_assist_open_question_response: str

    direct_lookup_classified: bool
    direct_lookup_assigned_code: str

    survey_assist_classified: bool
    survey_assist_assigned_code: str
    survey_assist_reasoning: str

    # 1..5
    survey_assist_alt_candidate_code_1: str
    survey_assist_alt_candidate_code_2: str
    survey_assist_alt_candidate_code_3: str
    survey_assist_alt_candidate_code_4: str
    survey_assist_alt_candidate_code_5: str

    survey_assist_alt_candidate_code_desc_1: str
    survey_assist_alt_candidate_code_desc_2: str
    survey_assist_alt_candidate_code_desc_3: str
    survey_assist_alt_candidate_code_desc_4: str
    survey_assist_alt_candidate_code_desc_5: str

    survey_assist_closed_question_response: str

    # 1..6: option labels from select_options
    survey_assist_closed_question_option_1: str
    survey_assist_closed_question_option_2: str
    survey_assist_closed_question_option_3: str
    survey_assist_closed_question_option_4: str
    survey_assist_closed_question_option_5: str
    survey_assist_closed_question_option_6: str

    time_start: str
    time_end: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__


def flatten_result(obj: dict[str, Any]) -> FlattenedRow:
    unique_id = str(obj.get("document_id", "") or "")
    user = str(obj.get("user", "") or "")
    time_start = str(obj.get("time_start", "") or "")
    time_end = str(obj.get("time_end", "") or "")

    first_response = _pick_first_response(obj)
    interactions = [
        it
        for it in _as_list(first_response.get("survey_assist_interactions"))
        if isinstance(it, dict)
    ]

    lookup_it = _find_interaction(interactions, "lookup") or {}
    classify_it = _find_interaction(interactions, "classify") or {}

    # Inputs: prefer classify inputs (often same as lookup), else lookup inputs
    inputs_map = _inputs_to_map(classify_it) or _inputs_to_map(lookup_it)

    job_title = str(inputs_map.get("job_title", "") or "")
    job_description = str(_normalize_job_desc_key(inputs_map) or "")
    org_description = str(inputs_map.get("org_description", "") or "")

    # Follow-up questions from classify response
    questions = _extract_followup_questions(classify_it)
    q0 = _get_question(questions, 0) or {}
    q1 = _get_question(questions, 1) or {}

    open_q_text = str(q0.get("text", "") or "")
    open_q_resp = str(q0.get("response", "") or "")

    closed_q_resp = str(q1.get("response", "") or "")
    select_options = _as_list(q1.get("select_options"))
    select_options_str = [str(x) for x in select_options if x is not None]
    select_options_str = _pad_list(select_options_str, 6, "")

    # Direct lookup classification fields
    lookup_found = bool(_safe_get(lookup_it, "response", "found", default=False))
    lookup_code = _safe_get(lookup_it, "response", "code", default="") or ""
    direct_lookup_assigned_code = str(lookup_code) if lookup_found else ""

    # Classify fields
    classified = bool(_safe_get(classify_it, "response", "classified", default=False))
    classify_code = _safe_get(classify_it, "response", "code", default="") or ""
    classify_reasoning = (
        _safe_get(classify_it, "response", "reasoning", default="") or ""
    )

    survey_assist_assigned_code = str(classify_code) if classified else ""
    survey_assist_reasoning = str(classify_reasoning) if classify_reasoning else ""

    # Candidates 1..5
    candidates = _as_list(_safe_get(classify_it, "response", "candidates", default=[]))
    cand_codes: list[str] = []
    cand_descs: list[str] = []
    for c in candidates:
        if isinstance(c, dict):
            cand_codes.append(str(c.get("code", "") or ""))
            cand_descs.append(str(c.get("description", "") or ""))

    cand_codes = _pad_list(cand_codes, 5, "")
    cand_descs = _pad_list(cand_descs, 5, "")

    return FlattenedRow(
        unique_id=unique_id,
        user=user,
        job_title=job_title,
        job_description=job_description,
        org_description=org_description,
        survey_assist_open_question=open_q_text,
        survey_assist_open_question_response=open_q_resp,
        direct_lookup_classified=lookup_found,
        direct_lookup_assigned_code=direct_lookup_assigned_code,
        survey_assist_classified=classified,
        survey_assist_assigned_code=survey_assist_assigned_code,
        survey_assist_reasoning=survey_assist_reasoning,
        survey_assist_alt_candidate_code_1=cand_codes[0],
        survey_assist_alt_candidate_code_2=cand_codes[1],
        survey_assist_alt_candidate_code_3=cand_codes[2],
        survey_assist_alt_candidate_code_4=cand_codes[3],
        survey_assist_alt_candidate_code_5=cand_codes[4],
        survey_assist_alt_candidate_code_desc_1=cand_descs[0],
        survey_assist_alt_candidate_code_desc_2=cand_descs[1],
        survey_assist_alt_candidate_code_desc_3=cand_descs[2],
        survey_assist_alt_candidate_code_desc_4=cand_descs[3],
        survey_assist_alt_candidate_code_desc_5=cand_descs[4],
        survey_assist_closed_question_response=closed_q_resp,
        survey_assist_closed_question_option_1=select_options_str[0],
        survey_assist_closed_question_option_2=select_options_str[1],
        survey_assist_closed_question_option_3=select_options_str[2],
        survey_assist_closed_question_option_4=select_options_str[3],
        survey_assist_closed_question_option_5=select_options_str[4],
        survey_assist_closed_question_option_6=select_options_str[5],
        time_start=time_start,
        time_end=time_end,
    )


def parse_api_payload(payload: Any) -> list[dict[str, Any]]:
    """Accept either:
    - a list of result objects
    - or {"results": [ ... ]}
    - or a single object (treated as one-row list)
    """
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        maybe_results = payload.get("results")
        if isinstance(maybe_results, list):
            return [x for x in maybe_results if isinstance(x, dict)]
        return [payload]
    return []


def write_csv(rows: list[FlattenedRow], out_path: str) -> None:
    if not rows:
        raise ValueError("No rows to write.")

    fieldnames = list(rows[0].as_dict().keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter=",",
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r.as_dict())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch survey-assist results and flatten to CSV."
    )
    parser.add_argument(
        "--base-url", default="http://0.0.0.0:8080", help="API base URL"
    )
    parser.add_argument("--wave-id", required=True, help="wave_id (e.g. 22-01-2026-1D)")
    parser.add_argument(
        "--survey-id", required=True, help="survey_id (e.g. shape_tomorrow_prototype)"
    )
    parser.add_argument("--out", default="", help="Optional CSV output path")
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="HTTP timeout seconds"
    )
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/v1/survey-assist/results"
    params = {"wave_id": args.wave_id, "survey_id": args.survey_id}

    try:
        resp = requests.get(url, params=params, timeout=args.timeout)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as e:
        print(f"HTTP error calling {url}: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Response was not valid JSON: {e}", file=sys.stderr)
        return 3

    result_objs = parse_api_payload(payload)
    flat_rows = [flatten_result(o) for o in result_objs]

    print(
        f"Fetched {len(result_objs)} result object(s). Flattened to {len(flat_rows)} row(s)."
    )

    if args.out:
        try:
            write_csv(flat_rows, args.out)
            print(f"Wrote CSV: {args.out}")
        except Exception as e:
            print(f"Failed writing CSV: {e}", file=sys.stderr)
            return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
