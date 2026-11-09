#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-run flaky analysis over attempt logs.

Reads reports/attempts/*.jsonl (one file per run), collapses each run to one
final status per case, and classifies the case across runs:

  stable_pass    every observed run was clean_pass
  stable_fail    every observed run failed (or broken)
  flaky          results differ across runs, or any run needed a retry
  new_fail       latest run failed while an earlier run passed
  fixed          latest run passed while an earlier run failed
  insufficient   only one run observed

It also cross-references artifacts/regression_quarantine.yaml so an
unregistered flaky case stays visible instead of being silently retried.
This tool is read-only: it never edits the quarantine registry.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ATTEMPTS_DIR = ROOT / "reports" / "attempts"
QUARANTINE = ROOT / "artifacts" / "regression_quarantine.yaml"
OUT_DIR = ROOT / "reports" / "flaky"

PASS_STATUSES = {"clean_pass", "retry_pass"}
FAIL_STATUSES = {"failed", "broken"}
PHASE_ORDER = {"setup": 0, "call": 1, "teardown": 2}


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def _load_records(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def _sort_key(record: dict[str, Any]) -> tuple[str, int, int]:
    return (
        str(record.get("recorded_at") or ""),
        int(record.get("attempt") or 0),
        PHASE_ORDER.get(str(record.get("phase")), 99),
    )


def _final_status(records: list[dict[str, Any]]) -> str:
    """Collapse one case in one run to a single status."""
    ordered = sorted(records, key=_sort_key)
    call = [r for r in ordered if r.get("phase") == "call"]
    if any(r.get("phase") in {"setup", "teardown"} and r.get("outcome") == "failed" for r in ordered):
        return "broken"
    if not call:
        if any(r.get("outcome") == "failed" for r in ordered):
            return "broken"
        if any(r.get("outcome") == "skipped" for r in ordered):
            return "skipped"
        return "broken"
    final = call[-1]
    if final.get("wasxfail") is not None:
        return "xfail"
    outcome = str(final.get("outcome") or "")
    if outcome == "passed":
        attempt = int(final.get("attempt") or 1)
        earlier_failed = any(str(r.get("outcome")) == "failed" for r in call[:-1])
        return "retry_pass" if (attempt > 1 and earlier_failed) else "clean_pass"
    if outcome == "skipped":
        return "skipped"
    return "failed"


def _load_quarantine() -> dict[str, dict[str, Any]]:
    if not QUARANTINE.exists():
        return {}
    raw = yaml.safe_load(QUARANTINE.read_text(encoding="utf-8")) or {}
    items = raw.get("quarantine") if isinstance(raw, dict) else None
    out: dict[str, dict[str, Any]] = {}
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and item.get("case_id"):
                out[str(item["case_id"])] = item
    return out


def _classify(history: list[str]) -> str:
    if len(history) <= 1:
        return "insufficient"
    observed = set(history)
    has_pass = bool(observed & PASS_STATUSES)
    has_fail = bool(observed & FAIL_STATUSES)
    # A run that needed a retry is flaky by definition.
    if "retry_pass" in observed:
        return "flaky"
    if has_pass and has_fail:
        last_fail = max(i for i, s in enumerate(history) if s in FAIL_STATUSES)
        first_pass = next((i for i, s in enumerate(history) if s in PASS_STATUSES), None)
        if last_fail == len(history) - 1:
            # still failing on the latest run
            return "new_fail"
        if first_pass is not None and first_pass < last_fail:
            # a pass happened, then it failed again => genuinely flaky
            return "flaky"
        # failures only at the start, passing ever since => fixed
        return "fixed"
    if observed <= PASS_STATUSES:
        return "stable_pass"
    if observed <= FAIL_STATUSES:
        return "stable_fail"
    return "flaky"


def _quarantine_state(case_id: str, registry: dict[str, dict[str, Any]], today: date) -> str:
    item = registry.get(case_id)
    if not item:
        return "unregistered"
    if str(item.get("status") or "active").lower() not in {"active", "quarantined"}:
        return "inactive"
    expires = item.get("expires_at")
    if expires:
        try:
            if date.fromisoformat(str(expires)[:10]) < today:
                return "expired"
        except ValueError:
            pass
    return "active"


def build_report(attempts_dir: Path, run_limit: int | None) -> dict[str, Any]:
    files = sorted(attempts_dir.glob("*.jsonl"))
    if run_limit:
        files = files[-run_limit:]

    per_run: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    run_time: dict[str, str] = {}
    for path in files:
        for record in _load_records(path):
            run_id = str(record.get("run_id") or "")
            test_id = str(record.get("test_id") or "")
            if not run_id or not test_id:
                continue
            per_run[run_id][test_id].append(record)
            run_time[run_id] = max(run_time.get(run_id, ""), str(record.get("recorded_at") or ""))

    ordered_runs = sorted(per_run.keys(), key=lambda r: run_time.get(r, ""))

    history: dict[str, list[tuple[str, str]]] = defaultdict(list)
    case_of: dict[str, str] = {}
    for run_id in ordered_runs:
        for test_id, records in per_run[run_id].items():
            history[test_id].append((run_id, _final_status(records)))
            for record in records:
                cid = str(record.get("case_id") or "")
                if cid and not cid.startswith("MISSING_CASE_ID:"):
                    case_of[test_id] = cid

    registry = _load_quarantine()
    today = _now().date()
    cases: list[dict[str, Any]] = []
    for test_id, runs in sorted(history.items()):
        statuses = [s for _r, s in runs]
        verdict = _classify(statuses)
        case_id = case_of.get(test_id, "")
        q_state = _quarantine_state(case_id, registry, today) if case_id else "no_case_id"
        cases.append({
            "test_id": test_id,
            "case_id": case_id,
            "verdict": verdict,
            "runs": len(runs),
            "statuses": statuses,
            "run_ids": [r for r, _s in runs],
            "quarantine": q_state,
        })

    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        counts[case["verdict"]] += 1

    needs_action = [
        case for case in cases
        if case["verdict"] in {"flaky", "new_fail", "stable_fail"}
        and case["quarantine"] in {"unregistered", "expired", "no_case_id"}
    ]

    return {
        "schema_version": "1.0",
        "generated_at": _now().isoformat(timespec="seconds"),
        "runs_analyzed": ordered_runs,
        "run_count": len(ordered_runs),
        "case_count": len(cases),
        "counts": dict(counts),
        "needs_action": needs_action,
        "cases": cases,
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        f"# Flaky Report - {report['generated_at']}",
        "",
        f"- Runs analyzed: {report['run_count']}",
        f"- Cases tracked: {report['case_count']}",
        "",
        "## Verdicts",
        "",
    ]
    for key in ("stable_pass", "flaky", "new_fail", "stable_fail", "fixed", "insufficient"):
        lines.append(f"- {key}: {counts.get(key, 0)}")
    lines.extend(["", "## Needs action (flaky / failing, not actively quarantined)", ""])
    if not report["needs_action"]:
        lines.append("- none")
    for case in report["needs_action"]:
        cid = case["case_id"] or "<no case_id>"
        lines.append(
            f"- [{case['verdict']}] {cid} ({case['quarantine']}) "
            f"history={' -> '.join(case['statuses'])}"
        )
    lines.append("")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-run flaky analysis")
    parser.add_argument("--attempts-dir", default=str(ATTEMPTS_DIR))
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--last", type=int, default=None, help="analyze only the last N runs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = _parse_args(argv)
    attempts_dir = Path(args.attempts_dir)
    if not attempts_dir.is_absolute():
        attempts_dir = ROOT / attempts_dir
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not any(attempts_dir.glob("*.jsonl")):
        message = f"no attempt logs found under {attempts_dir}"
        (out_dir / "flaky_report.json").write_text(json.dumps({"error": message}, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "flaky_report.md").write_text(f"# Flaky Report\n\n{message}\n", encoding="utf-8")
        print(f"[flaky_report] {message}")
        return 2

    report = build_report(attempts_dir, args.last)
    (out_dir / "flaky_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "flaky_report.md").write_text(render_markdown(report), encoding="utf-8")
    counts = report["counts"]
    print(
        f"[flaky_report] runs={report['run_count']} cases={report['case_count']} "
        f"flaky={counts.get('flaky', 0)} new_fail={counts.get('new_fail', 0)} "
        f"stable_fail={counts.get('stable_fail', 0)} needs_action={len(report['needs_action'])}"
    )
    print(f"[flaky_report] {out_dir / 'flaky_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())