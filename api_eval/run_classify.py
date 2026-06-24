#### STEVE REMINDER - add , { include = "api_eval" } to pyproject.toml

from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from api_eval.classify_body import load_rows, render_body_from_template
from api_eval.classify_validators import (
    ALT_CANDIDATE_CODES_MATCH,
    CANDIDATE_CODES_COUNT,
    CLASSIFIED_VALUE,
    CODE_VALUE,
    validate_row,
)


def _build_headers() -> dict[str, str]:
    headers: dict[str, str] = {"content-type": "application/json"}
    token = os.getenv("API_TOKEN")
    if token:
        headers["authorization"] = f"Bearer {token}"
    return headers


def _utc_run_id() -> str:
    # Example: 20260123T142233Z_6f3a2c1b
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


def _safe_id(value: str) -> str:
    # safe for filenames/logs
    value = value.strip()
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return value[:120] if value else "unknown"


def _open_jsonl_writer(out_dir: Path, run_id: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"classify_responses_{run_id}.jsonl"
    # touch the file early so you can see it even if run fails quickly
    out_path.write_text("", encoding="utf-8")
    return out_path


def _append_jsonl(out_path: Path, record: dict[str, Any]) -> None:
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


RULES = [CLASSIFIED_VALUE, CODE_VALUE, CANDIDATE_CODES_COUNT, ALT_CANDIDATE_CODES_MATCH]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url", default=os.getenv("API_URL", "http://0.0.0.0:8080")
    )
    parser.add_argument("--path", default="/v1/survey-assist/classify")
    parser.add_argument("--csv", default="data/test_eval.csv")
    parser.add_argument("--template", default="api_eval/template_classify_body.json")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--fail-fast", action="store_true")

    # Output controls
    parser.add_argument("--save-responses", action="store_true")
    parser.add_argument(
        "--out-dir", default=os.getenv("API_EVAL_OUT_DIR", "scripts/output")
    )
    parser.add_argument("--run-id", default=os.getenv("API_EVAL_RUN_ID", ""))

    args = parser.parse_args()

    url = args.base_url.rstrip("/") + args.path
    rows = load_rows(args.csv)
    headers = _build_headers()

    run_id = args.run_id.strip() or _utc_run_id()
    out_path: Path | None = None

    if args.save_responses:
        out_path = _open_jsonl_writer(Path(args.out_dir), run_id)
        print(f"Saving responses to: {out_path}")

        # Write a header/meta record (optional but handy)
        _append_jsonl(
            out_path,
            {
                "record_type": "run_meta",
                "run_id": run_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "url": url,
                "csv": str(args.csv),
                "template": str(args.template),
            },
        )

    failures: list[str] = []
    failed_ids: set[str] = set()
    classified_value_failure_count = 0
    classified_value_failed_ids: set[str] = set()
    with httpx.Client(timeout=args.timeout) as client:
        for i, row in enumerate(rows, start=1):
            body = render_body_from_template(args.template, row)
            print(f"[REQUEST BODY] {json.dumps(body)}")
            unique_id = _safe_id(str(row.get("unique_id", f"row_{i}")))

            record_base: dict[str, Any] = {
                "record_type": "row_result",
                "run_id": run_id,
                "row_number": i,
                "unique_id": unique_id,
            }
            print(f"\nRunning test {i} of {len(rows)}: {unique_id}")
            try:
                r = client.post(url, json=body, headers=headers)
                print(f"Sent request for {unique_id} to {url}")
            except Exception as e:
                msg = f"{unique_id}: request failed: {e}"
                failures.append(msg)
                failed_ids.add(unique_id)
                print("FAIL", msg)

                if out_path:
                    _append_jsonl(
                        out_path,
                        {
                            **record_base,
                            "ok": False,
                            "error": str(e),
                            # optional: store body (can be large; remove if you prefer)
                            "request_body": body,
                        },
                    )

                if args.fail_fast:
                    return 2
                continue

            # Try to parse JSON, but don't crash if it's non-JSON error text
            response_json: Any | None = None
            response_text: str | None = None
            try:
                response_json = r.json()
            except Exception:
                response_text = r.text

            if r.status_code != 200:
                msg = f"{unique_id}: HTTP {r.status_code}: {(response_text or str(response_json))[:300]}"
                failures.append(msg)
                failed_ids.add(unique_id)
                print("FAIL", msg)

                if out_path:
                    _append_jsonl(
                        out_path,
                        {
                            **record_base,
                            "ok": False,
                            "status_code": r.status_code,
                            "response_json": response_json,
                            "response_text": response_text,
                            "request_body": body,
                        },
                    )

                if args.fail_fast:
                    return 2
                continue

            # Basic shape validation: should have "results" list etc.
            data: Any = response_json
            ok_shape = isinstance(data, dict) and isinstance(data.get("results"), list)
            if not ok_shape:
                msg = f"{unique_id}: unexpected response shape: {str(data)[:300]}"
                failures.append(msg)
                failed_ids.add(unique_id)
                print("FAIL", msg)

                if out_path:
                    _append_jsonl(
                        out_path,
                        {
                            **record_base,
                            "ok": False,
                            "status_code": r.status_code,
                            "shape_ok": False,
                            "response_json": response_json,
                            "response_text": response_text,
                            "request_body": body,
                        },
                    )

                if args.fail_fast:
                    return 2
            else:
                failures_for_row, warnings_for_row = validate_row(row, data, RULES)

                row_ok = len(failures_for_row) == 0

                for vf in failures_for_row:
                    msg = f"{unique_id}: {vf.rule_id} failed. expected={vf.expected!r} actual={vf.actual!r}"
                    failures.append(msg)
                    failed_ids.add(unique_id)

                    if vf.rule_id == "classified.value":
                        classified_value_failure_count += 1
                        classified_value_failed_ids.add(unique_id)
                    print("FAIL", msg)

                for vw in warnings_for_row:
                    print(
                        "WARN",
                        f"{unique_id}: {vw.rule_id} {vw.message} "
                        f"expected_order={vw.expected!r} received_order={vw.actual!r}",
                    )

                if row_ok:
                    print("PASS", f"{unique_id}: all validations passed")

                if args.fail_fast:
                    return 2

                if out_path:
                    _append_jsonl(
                        out_path,
                        {
                            **record_base,
                            "ok": row_ok,  # ✅ correct now
                            "status_code": r.status_code,
                            "shape_ok": True,
                            "response_json": response_json,
                            "response_text": response_text,
                            "validation_failures": [
                                f.__dict__ for f in failures_for_row
                            ],
                            "validation_warnings": [
                                w.__dict__ for w in warnings_for_row
                            ],
                        },
                    )

    if out_path:
        total_rows = len(rows)
        failed_rows = len(failed_ids)
        passed_rows = total_rows - failed_rows

        ratio_str = (
            f"{passed_rows}/{failed_rows}" if failed_rows else f"{passed_rows}/0"
        )
        _append_jsonl(
            out_path,
            {
                "record_type": "run_summary",
                "run_id": run_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "total_rows": len(rows),
                "passed_rows": passed_rows,
                "failed_rows": failed_rows,
                "pass_fail_ratio": f"{passed_rows}:{failed_rows}",
                "failed_ids": sorted(failed_ids),
                "classified_value_failures": classified_value_failure_count,
                "classified_value_failed_rows": len(classified_value_failed_ids),
                "classified_value_failed_ids": sorted(classified_value_failed_ids),
            },
        )

    print(
        f"\nRun summary: {total_rows} rows — "
        f"{passed_rows} passed, {failed_rows} failed,"
        f"{classified_value_failure_count} classified value failures"
    )
    if failed_ids:
        print("\n--- Failed rows ---")
        for uid in sorted(failed_ids):
            print(uid)

        print("\n--- Failure details ---")
        for f in failures:
            print(f)
        return 2

    print("\nAll rows passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
