from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SKIP = object()


def _to_bool(value: Any) -> bool | None:
    """Convert common CSV-ish representations into bool.
    Returns None if value is missing/blank/unparseable.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().upper()
    if s in {"TRUE", "T", "1", "YES", "Y"}:
        return True
    if s in {"FALSE", "F", "0", "NO", "N"}:
        return False
    if s in {"", "NAN", "NONE"}:
        return None
    return None


def _to_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    if s.upper() in {"NONE", "NULL", "NAN"}:
        return None
    return s


def _count_populated_alt_candidate_codes(row: dict[str, Any]) -> int:
    count = 0
    for i in range(1, 6):
        value = row.get(f"survey_assist_alt_candidate_code_{i}")
        if _to_str_or_none(value) is not None:
            count += 1
    return count


def _get_first_result(response_json: dict[str, Any]) -> dict[str, Any]:
    results = response_json.get("results")
    if not isinstance(results, list) or not results:
        return {}
    first = results[0]
    return first if isinstance(first, dict) else {}


@dataclass(frozen=True)
class ValidationWarning:
    rule_id: str
    message: str
    expected: Any
    actual: Any


@dataclass(frozen=True)
class ValidationFailure:
    rule_id: str
    message: str
    expected: Any
    actual: Any


@dataclass(frozen=True)
class Rule:
    rule_id: str
    description: str
    expected: Callable[[dict[str, Any]], Any]  # from CSV row
    actual: Callable[[dict[str, Any]], Any]  # from API response JSON
    compare: Callable[[Any, Any], bool]  # expected vs actual
    on_missing_expected: str = "skip"  # "skip" or "fail"


@dataclass(frozen=True)
class CompoundRule:
    rule_id: str
    description: str
    check: Callable[
        [dict[str, Any], dict[str, Any]],
        tuple[list[ValidationFailure], list[ValidationWarning]],
    ]


def validate_row(
    row: dict[str, Any],
    response_json: dict[str, Any],
    rules: list[Any],
) -> tuple[list[ValidationFailure], list[ValidationWarning]]:
    failures: list[ValidationFailure] = []
    warnings: list[ValidationWarning] = []

    for rule in rules:
        if isinstance(rule, Rule):
            exp = rule.expected(row)

            print(f"[VALIDATE] rule={rule.rule_id} expected={exp!r}")

            if exp is SKIP:
                print(f"[VALIDATE] rule={rule.rule_id} skipped")
                continue

            if exp is None and rule.on_missing_expected == "skip":
                print(f"[VALIDATE] rule={rule.rule_id} skipped")
                continue

            act = rule.actual(response_json)

            print(f"[VALIDATE] rule={rule.rule_id} actual={act!r}")

            if not rule.compare(exp, act):
                failures.append(
                    ValidationFailure(
                        rule_id=rule.rule_id,
                        message=rule.description,
                        expected=exp,
                        actual=act,
                    )
                )

    f, w = rule.check(row, response_json)
    failures.extend(f)
    warnings.extend(w)

    if f or w:
        print(f"[VALIDATE] rule={rule.rule_id} " f"failures={len(f)} warnings={len(w)}")

    return failures, warnings


# ---- extensible rules ----


def expected_classified_from_csv(row: dict[str, Any]) -> bool | None:
    """Your rule:
      - when both direct_lookup_classified and survey_assist_classified are FALSE,
        the API should return classified == False.

    This function returns:
      - False when both are explicitly False
      - True when one or both are explicitly True
      - None if the columns are missing/blank/unparseable
    """
    dl = _to_bool(row.get("direct_lookup_classified"))
    sa = _to_bool(row.get("survey_assist_classified"))

    # Only validate when both values are present
    if dl is None or sa is None:
        return None

    # If either is TRUE → classified must be TRUE
    if dl is True or sa is True:
        return True
    else:
        # Both are FALSE → classified must be FALSE
        return False


def actual_classified_from_response(resp_json: dict[str, Any]) -> Any:
    first = _get_first_result(resp_json)
    return first.get("classified")


CLASSIFIED_VALUE = Rule(
    rule_id="classified.value",
    description="response.results[0].classified must be False when both direct_lookup_classified and survey_assist_classified are FALSE, otherwise True",
    expected=expected_classified_from_csv,
    actual=actual_classified_from_response,
    compare=lambda exp, act: act
    is exp,  # strict identity: must be actual False (not 'false' string)
    on_missing_expected="skip",
)


def expected_code_from_csv(row: dict[str, Any]) -> str | None:
    dl = _to_bool(row.get("direct_lookup_classified"))
    sa = _to_bool(row.get("survey_assist_classified"))

    # Skip if direct lookup is True (your rule)
    if dl is True:
        return SKIP

    # Only validate if we can interpret both booleans
    if dl is None or sa is None:
        return SKIP

    # DL False, SA False -> code must be null
    if dl is False and sa is False:
        return None

    # DL False, SA True -> code must match CSV assigned code
    if dl is False and sa is True:
        return _to_str_or_none(row.get("survey_assist_assigned_code"))

    # Any other combination not specified: skip (defensive)
    return SKIP


def actual_code_from_response(resp_json: dict[str, Any]) -> str | None:
    first = _get_first_result(resp_json)
    return _to_str_or_none(first.get("code"))


CODE_VALUE = Rule(
    rule_id="code.value",
    description=(
        "When direct_lookup_classified is FALSE: "
        "(a) if survey_assist_classified is FALSE, response.results[0].code must be null; "
        "(b) if survey_assist_classified is TRUE, response.results[0].code must equal survey_assist_assigned_code."
        " When direct_lookup_classified is TRUE, validation is skipped."
    ),
    expected=expected_code_from_csv,
    actual=actual_code_from_response,
    compare=lambda exp, act: exp == act,
    on_missing_expected="skip",
)


def actual_candidates_count_from_response(resp_json: dict[str, Any]) -> int:
    first = _get_first_result(resp_json)
    candidates = first.get("candidates")

    if candidates is None:
        return 0

    if not isinstance(candidates, list):
        return 0

    return len(candidates)


CANDIDATE_CODES_COUNT = Rule(
    rule_id="candidate_codes.count",
    description=(
        "The number of objects in response.results[0].candidates must match the "
        "number of populated survey_assist_alt_candidate_code_1..5 columns in the CSV."
    ),
    expected=lambda row: _count_populated_alt_candidate_codes(row),
    actual=actual_candidates_count_from_response,
    compare=lambda exp, act: exp == act,
)


def expected_alt_candidate_codes(row: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for i in range(1, 6):
        v = _to_str_or_none(row.get(f"survey_assist_alt_candidate_code_{i}"))
        if v is not None:
            codes.append(v)
    return codes


def received_candidate_codes(resp_json: dict[str, Any]) -> list[str]:
    first = _get_first_result(resp_json)
    candidates = first.get("candidates")
    if not isinstance(candidates, list):
        return []
    out: list[str] = []
    for c in candidates:
        if isinstance(c, dict):
            code = _to_str_or_none(c.get("code"))
            if code is not None:
                out.append(code)
    return out


def check_alt_candidate_codes(
    row: dict[str, Any], resp_json: dict[str, Any]
) -> tuple[list[ValidationFailure], list[ValidationWarning]]:
    expected = expected_alt_candidate_codes(row)
    received = received_candidate_codes(resp_json)

    exp_set = set(expected)
    rec_set = set(received)

    failures: list[ValidationFailure] = []
    warnings: list[ValidationWarning] = []

    # Always include these in any message / record
    payload_expected_vs_received = {
        "expected_order": expected,
        "received_order": received,
    }

    # FAIL if any expected code is missing from response
    missing = sorted(exp_set - rec_set)
    extra = sorted(rec_set - exp_set)

    if missing or extra:
        failures.append(
            ValidationFailure(
                rule_id="alt_candidate.codes_match_set",
                message=(
                    "Candidate codes do not match expected set. "
                    f"missing={missing} extra={extra}"
                ),
                expected=payload_expected_vs_received["expected_order"],
                actual=payload_expected_vs_received["received_order"],
            )
        )
        return failures, warnings

    # Sets match → pass, but warn if order differs
    if expected != received:
        warnings.append(
            ValidationWarning(
                rule_id="alt_candidate.codes_match_order",
                message="Candidate codes match but order differs.",
                expected=payload_expected_vs_received["expected_order"],
                actual=payload_expected_vs_received["received_order"],
            )
        )

    return failures, warnings


ALT_CANDIDATE_CODES_MATCH = CompoundRule(
    rule_id="alt_candidate.codes_match",
    description=(
        "All expected alt candidate codes from CSV must appear in response.candidates (order-independent). "
        "Warn if order differs."
    ),
    check=check_alt_candidate_codes,
)
