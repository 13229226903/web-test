#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize attempt-level pytest records into an honest regression report.

States
------
clean_pass
    The test passed on its first call attempt.
retry_pass
    The test failed on an earlier call attempt and passed on a later attempt.
quarantined
    The case is listed as an active quarantine in the quarantine registry.  It
    is visible in the report, excluded from the release gate, and never counted
    as a pass.
failed
    The final call attempt failed.
broken
    Setup/teardown failed without a passing call (or the test never reached a
    call phase).
skipped
    The test was skipped for environment/data/permission/authorization reasons.
xfail
    The test was expected to fail (`wasxfail`).  This is not a pass and is
    reported separately so known product defects cannot masquerade as green.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from case_id_rules import case_id_from_title  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTEMPT_LOG = ROOT / "reports" / "attempts" / "attempts.jsonl"
DEFAULT_QUARANTINE = ROOT / "artifacts" / "regression_quarantine.yaml"

STATUS_ORDER = ("clean_pass", "retry_pass", "quarantined", "xfail", "skipped", "failed", "broken")
GATE_FAIL_STATUSES = {"retry_pass", "failed", "broken"}
PHASE_ORDER = {"setup": 0, "call": 1, "teardown": 2}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate clean/retry/quarantine regression summary")
    parser.add_argument("--attempt-log", default=str(DEFAULT_ATTEMPT_LOG), help="JSONL written by regression_governance.py")
    parser.add_argument("--quarantine", default=str(DEFAULT_QUARANTINE), help="quarantine registry YAML")
    parser.add_argument("--run-id", default=None, help="run_id to summarize; defaults to latest by recorded_at")
    parser.add_argument("--out-dir", default=None, help="output directory; defaults next to the attempt log")
    parser.add_argument("--allure-dir", default=None, help="optional Allure results dir used to recover dynamic titles")
    parser.add_argument("--gate-mode", choices=("strict", "allow-retry", "report-only"), default="strict",
                        help="strict fails on retry/xfail/failure; allow-retry permits retry_pass; report-only never fails")
    parser.add_argument("--fail-on-skipped", action="store_true", help="treat skipped cases as gate failures")
    parser.add_argument("--fail-on-xfail", action="store_true", help="treat expected failures as gate failures")
    parser.add_argument("--max-retry-pass-rate", type=float, default=None,
                        help="optional strict gate threshold, e.g. 0.02")
    return parser.parse_args(argv)


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _load_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"attempt log not found: {path}")
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            # A malformed line means a torn write; keep the run visible rather
            # than silently discarding evidence.
            records.append({
                "schema_version": "1.0",
                "run_id": "malformed",
                "recorded_at": "",
                "test_id": f"<malformed-line-{line_no}>",
                "case_id": f"<malformed-line-{line_no}>",
                "phase": "unknown",
                "attempt": 1,
                "outcome": "failed",
                "duration_s": 0,
                "worker": "unknown",
                "base_url": "",
                "markers": [],
                "error": line[:500],
                "_malformed": True,
            })
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _resolve_run_id(records: Iterable[dict[str, Any]], requested: str | None) -> str:
    if requested:
        return requested
    latest: tuple[str, str] | None = None
    for record in records:
        run_id = str(record.get("run_id") or "")
        recorded_at = str(record.get("recorded_at") or "")
        if not run_id:
            continue
        if latest is None or recorded_at > latest[1]:
            latest = (run_id, recorded_at)
    if latest is None:
        raise SystemExit("no run_id found in attempt log")
    return latest[0]


def _load_quarantine(path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not path.exists():
        return {}, []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    items = raw.get("quarantine") if isinstance(raw, dict) else None
    if items is None:
        return {}, [f"quarantine registry has no 'quarantine' list: {path}"]
    if not isinstance(items, list):
        return {}, [f"quarantine must be a list: {path}"]
    by_case: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("case_id"):
            errors.append(f"quarantine[{index}] missing case_id")
            continue
        case_id = str(item["case_id"])
        if case_id in by_case:
            errors.append(f"duplicate quarantine case_id: {case_id}")
        by_case[case_id] = item
    return by_case, errors


def _is_active_quarantine(item: dict[str, Any] | None, today: date) -> bool:
    if not item:
        return False
    if str(item.get("status") or "active").lower() not in {"active", "quarantined"}:
        return False
    expires_at = item.get("expires_at")
    if not expires_at:
        return True
    try:
        expiry = date.fromisoformat(str(expires_at)[:10])
    except ValueError:
        return True
    return expiry >= today


def _sort_key(record: dict[str, Any]) -> tuple[str, int, int, str]:
    return (
        str(record.get("recorded_at") or ""),
        int(record.get("attempt") or 0),
        PHASE_ORDER.get(str(record.get("phase")), 99),
        str(record.get("phase") or ""),
    )


def _classify(records: list[dict[str, Any]], quarantine: dict[str, Any] | None, today: date) -> tuple[str, str]:
    if _is_active_quarantine(quarantine, today):
        return "quarantined", "listed in active quarantine registry"

    call_records = [r for r in records if r.get("phase") == "call"]
    final_call = call_records[-1] if call_records else None

    # Setup/teardown failures make the case broken even if the call phase
    # passed: a fixture error is a real failure and must never become
    # clean_pass.  This includes pytest ERROR exit codes (teardown failures).
    setup_teardown_failed = any(
        r.get("phase") in {"setup", "teardown"} and str(r.get("outcome")) == "failed"
        for r in records
    )

    if final_call is not None:
        if setup_teardown_failed:
            return "broken", _error_summary(records[-1] if records else {})
        if final_call.get("wasxfail") is not None:
            return "xfail", str(final_call.get("wasxfail") or "expected failure")
        outcome = str(final_call.get("outcome") or "")
        if outcome == "passed":
            attempt = int(final_call.get("attempt") or 1)
            earlier_failed = any(str(r.get("outcome")) == "failed" for r in call_records[:-1])
            if attempt > 1 and earlier_failed:
                return "retry_pass", f"passed on attempt {attempt} after an earlier failure"
            return "clean_pass", "passed on first call attempt"
        if outcome == "skipped":
            return "skipped", "call phase skipped"
        return "failed", _error_summary(final_call)

    # No call phase: setup/teardown failures are broken; skipped setup is skipped.
    if any(str(r.get("outcome")) == "failed" for r in records):
        return "broken", _error_summary(records[-1] if records else {})
    if any(str(r.get("outcome")) == "skipped" for r in records):
        return "skipped", "setup/teardown skipped"
    return "broken", "no call result recorded"


def _error_summary(record: dict[str, Any]) -> str:
    text = str(record.get("error") or "").strip().replace("\r", "")
    if not text:
        return "no error detail"
    return " ".join(text.splitlines()[-2:])[:240]


def _allure_meta_index(allure_dir: Path | None) -> dict[str, dict[str, str]]:
    """Map normalized pytest node paths to final Allure title + case_id label.

    Two things are only visible in Allure result JSON, not in pytest hooks:
      * ``allure.dynamic.title`` (final display name)
      * ``allure.dynamic.label("case_id", ...)`` (runtime label)

    ``@allure.label("case_id", ...)`` becomes a pytest marker and is read by the
    recorder, but the dynamic form is not.  Reading the Allure JSON here is what
    keeps the coverage number honest for tests that set the label at runtime.
    """
    if not allure_dir or not allure_dir.exists():
        return {}
    index: dict[str, dict[str, str]] = {}
    for result_path in sorted(allure_dir.glob("*-result.json")):
        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        full_name = str(data.get("fullName") or "")
        if not full_name:
            continue
        title = str(data.get("name") or "")
        case_id = ""
        for label in data.get("labels") or []:
            if isinstance(label, dict) and str(label.get("name")) == "case_id":
                case_id = str(label.get("value") or "")
                break
        if not title and not case_id:
            continue
        key = _normalize_node_key(full_name)
        index[key] = {"title": title, "case_id": case_id}
        # pytest nodeids include parameter brackets and file suffix; Allure
        # fullName is dotted/hash-like. Index trailing segments so a caller can
        # match by suffix even when prefixes differ.
        parts = key.split("/")
        for start in range(1, len(parts)):
            index.setdefault("/".join(parts[start:]), {"title": title, "case_id": case_id})
    return index


def _lookup_meta(index: dict[str, dict[str, str]], node_key: str) -> dict[str, str]:
    """Exact match first, then progressively shorter trailing-segment match."""
    if node_key in index:
        return index[node_key]
    parts = node_key.split("/")
    for start in range(1, len(parts)):
        candidate = "/".join(parts[start:])
        if candidate in index:
            return index[candidate]
    return {}


def _normalize_node_key(value: str) -> str:
    value = value.replace("\\\\", "/").replace(".", "/")
    value = value.replace("::", "/").replace("#", "/")
    parts = [part for part in value.split("/") if part]
    return "/".join(parts).lower()


def build_summary(attempt_log: Path, quarantine_path: Path, requested_run_id: str | None, allure_dir: Path | None = None) -> dict[str, Any]:
    records = _load_attempts(attempt_log)
    run_id = _resolve_run_id(records, requested_run_id)
    selected = [r for r in records if str(r.get("run_id")) == run_id]
    if not selected:
        raise SystemExit(f"run_id not found in attempt log: {run_id}")

    allure_meta = _allure_meta_index(allure_dir)
    quarantine, registry_errors = _load_quarantine(quarantine_path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in selected:
        group_key = str(record.get("test_id") or record.get("case_id") or "<unknown>")
        grouped[group_key].append(record)
    cases: list[dict[str, Any]] = []
    today = _now().date()
    for test_id, group in sorted(grouped.items()):
        group.sort(key=_sort_key)
        node_key = _normalize_node_key(test_id)
        meta = _lookup_meta(allure_meta, node_key)
        allure_title = str(meta.get("title") or "")
        allure_case_id = str(meta.get("case_id") or "")
        title = str(group[-1].get("title") or allure_title or "")

        # case_id precedence:
        #   1. recorder marker  (@allure.label / allure.label via pytest marker)
        #   2. Allure result label  (covers allure.dynamic.label at runtime)
        #   3. strict title extraction (namespaced for short ids)
        #   4. visible MISSING debt (never guess)
        recorded_case_id = str(group[-1].get("case_id") or "")
        marker_resolved = bool(recorded_case_id) and not recorded_case_id.startswith("MISSING_CASE_ID:")
        if marker_resolved:
            case_id = recorded_case_id
            resolved_case_id = True
            case_id_source = "label_marker"
        elif allure_case_id:
            case_id = allure_case_id
            resolved_case_id = True
            case_id_source = "label_allure_json"
        else:
            extracted = case_id_from_title(title, test_id)
            if extracted:
                case_id = extracted
                resolved_case_id = True
                case_id_source = "title_extracted"
            else:
                case_id = recorded_case_id or test_id
                resolved_case_id = False
                case_id_source = "missing";
        status, reason = _classify(group, quarantine.get(case_id), today)
        call_records = [r for r in group if r.get("phase") == "call"]
        first_failure = next((r for r in call_records if r.get("outcome") == "failed"), None)
        cases.append({
            "test_id": test_id,
            "case_id": case_id,
            "case_id_resolved": resolved_case_id,
            "case_id_source": case_id_source,
            "title": title,
            "status": status,
            "reason": reason,
            "attempts": max([int(r.get("attempt") or 0) for r in group] or [0]),
            "duration_s": round(sum(float(r.get("duration_s") or 0.0) for r in group), 3),
            "base_url": str(group[-1].get("base_url") or ""),
            "worker": str(group[-1].get("worker") or "master"),
            "first_failure_at": str(first_failure.get("recorded_at") if first_failure else ""),
            "first_failure_error": _error_summary(first_failure or {}),
            "quarantine": quarantine.get(case_id),
        })
    counts = Counter(case["status"] for case in cases)
    total = len(cases)
    case_id_resolved = sum(1 for case in cases if case["case_id_resolved"])
    case_id_missing = total - case_id_resolved
    clean = counts["clean_pass"]
    retry = counts["retry_pass"]
    retry_rate = round(retry / total, 6) if total else 0.0
    gate_counts = {status: counts[status] for status in STATUS_ORDER}
    return {
        "schema_version": "1.0",
        "generated_at": _now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "base_urls": sorted({case["base_url"] for case in cases if case["base_url"]}),
        "attempt_log": str(attempt_log),
        "quarantine_registry": str(quarantine_path),
        "registry_errors": registry_errors,
        "total": total,
        "counts": gate_counts,
        "case_id_coverage": {
            "resolved": case_id_resolved,
            "missing": case_id_missing,
            "coverage_rate": round(case_id_resolved / total, 6) if total else 0.0,
        },
        "rates": {
            "clean_pass_rate": round(clean / total, 6) if total else 0.0,
            "retry_pass_rate": retry_rate,
            "quarantined_rate": round(counts["quarantined"] / total, 6) if total else 0.0,
        },
        "cases": cases,
    }


def gate_violations(summary: dict[str, Any], gate_mode: str, fail_on_skipped: bool,
                    fail_on_xfail: bool, max_retry_pass_rate: float | None) -> list[str]:
    if gate_mode == "report-only":
        return []
    violations: list[str] = []
    statuses = set(GATE_FAIL_STATUSES)
    if gate_mode != "strict":
        statuses.discard("retry_pass")
    if fail_on_skipped:
        statuses.add("skipped")
    if fail_on_xfail:
        statuses.add("xfail")
    for case in summary["cases"]:
        if case["status"] in statuses:
            violations.append(f"{case['case_id']}: {case['status']} - {case['reason']}")
    for error in summary.get("registry_errors", []):
        violations.append(f"quarantine registry: {error}")
    if max_retry_pass_rate is not None and summary["rates"]["retry_pass_rate"] > max_retry_pass_rate:
        violations.append(
            f"retry_pass_rate {summary['rates']['retry_pass_rate']:.4f} exceeds max {max_retry_pass_rate:.4f}"
        )
    return violations
def render_markdown(summary: dict[str, Any], violations: list[str], gate_mode: str) -> str:
    counts = summary["counts"]
    rates = summary["rates"]
    lines = [
        f"# Regression Summary - {summary['run_id']}",
        "",
        f"- Generated: {summary['generated_at']}",
        f"- Base URL: {', '.join(summary['base_urls']) or 'n/a'}",
        f"- Gate mode: {gate_mode}",
        f"- Total: {summary['total']}",
        f"- clean_pass: {counts['clean_pass']}",
        f"- retry_pass: {counts['retry_pass']}",
        f"- quarantined: {counts['quarantined']}",
        f"- xfail: {counts['xfail']}",
        f"- skipped: {counts['skipped']}",
        f"- failed: {counts['failed']}",
        f"- broken: {counts['broken']}",
        f"- clean_pass_rate: {rates['clean_pass_rate']:.4f}",
        f"- retry_pass_rate: {rates['retry_pass_rate']:.4f}",
        f"- case_id_coverage: {summary['case_id_coverage']['resolved']}/{summary['total']} "
        f"({summary['case_id_coverage']['coverage_rate']:.4f})",
        "",
        "## Gate",
        "",
    ]
    lines.extend([f"- FAIL: {item}" for item in violations] or ["- PASS"])
    lines.extend(["", "## Non-clean cases", ""])
    non_clean = [case for case in summary["cases"] if case["status"] != "clean_pass"]
    if not non_clean:
        lines.append("- none")
    for case in non_clean:
        lines.append(
            f"- [{case['status']}] {case['case_id']} {case['title']} "
            f"(attempts={case['attempts']}) - {case['reason']}"
        )
    lines.extend(["", "## MISSING_CASE_ID debt", ""])
    missing_cases = [case for case in summary["cases"] if not case.get("case_id_resolved")]
    if not missing_cases:
        lines.append("- none")
    else:
        for case in missing_cases:
            lines.append(f"- {case['test_id']}")
    lines.append("")
    return "\n".join(lines)
def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    attempt_log = Path(args.attempt_log)
    if not attempt_log.is_absolute():
        attempt_log = ROOT / attempt_log
    quarantine_path = Path(args.quarantine)
    if not quarantine_path.is_absolute():
        quarantine_path = ROOT / quarantine_path
    out_dir = Path(args.out_dir) if args.out_dir else attempt_log.parent
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    allure_dir = Path(args.allure_dir) if args.allure_dir else None
    if allure_dir is not None and not allure_dir.is_absolute():
        allure_dir = ROOT / allure_dir
    summary = build_summary(attempt_log, quarantine_path, args.run_id, allure_dir)
    violations = gate_violations(summary, args.gate_mode, args.fail_on_skipped, args.fail_on_xfail, args.max_retry_pass_rate)
    summary["gate"] = {
        "mode": args.gate_mode,
        "status": "failed" if violations else "passed",
        "violations": violations,
        "fail_on_skipped": args.fail_on_skipped,
        "fail_on_xfail": args.fail_on_xfail,
        "max_retry_pass_rate": args.max_retry_pass_rate,
    }
    json_path = out_dir / "regression_summary.json"
    md_path = out_dir / "regression_summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(summary, violations, args.gate_mode), encoding="utf-8")
    print(f"[regression_summary] {json_path}")
    print(f"[regression_summary] {md_path}")
    print(
        f"[regression_summary] total={summary['total']} clean={summary['counts']['clean_pass']} "
        f"retry={summary['counts']['retry_pass']} quarantined={summary['counts']['quarantined']} "
        f"failed={summary['counts']['failed']} broken={summary['counts']['broken']} "
        f"skipped={summary['counts']['skipped']} gate={summary['gate']['status']}"
    )
    return 1 if violations else 0
if __name__ == "__main__":
    raise SystemExit(main())


