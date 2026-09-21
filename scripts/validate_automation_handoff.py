#!/usr/bin/env python3
"""Validate the exploration -> cases -> test-writing handoff.

The validator intentionally checks only the cross-role contract. It does not
replace sync.md/cases.md human review or page-map exploration.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"pending_review", "ready_for_case_design", "implementation_ready", "blocked"}
IMPLEMENTATION_REQUIRED = {
    "case_id", "source_case", "source_evidence", "platform", "viewport", "environment",
    "account", "data", "entry", "state_chain", "actions", "event_capture", "evidence",
    "implementation_status",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def resolve_repo_path(path_value: str, base: Path = ROOT) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else base / path


def read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1]) or {}
    return data if isinstance(data, dict) else {}


def case_ids(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    # Covers normal matrix rows such as | P-NEW-01 | and avoids AC-001 rows.
    return set(re.findall(r"\|\s*([PM]-[A-Z0-9-]+)\s*\|", text))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def ref_exists(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    value = value.strip()
    if "<" in value or value.startswith(("http://", "https://", "user_decision:", "task:")):
        return False
    path_part = value.split("#", 1)[0]
    return resolve_repo_path(path_part).exists()


def add_error(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_contract(contract: dict[str, Any], index: int, errors: list[str]) -> None:
    prefix = f"contracts[{index}]"
    missing = sorted(IMPLEMENTATION_REQUIRED - contract.keys())
    if missing:
        add_error(errors, f"{prefix}: missing {', '.join(missing)}")
    case_id = contract.get("case_id", "<unknown>")
    source_evidence = as_list(contract.get("source_evidence"))
    if not source_evidence:
        add_error(errors, f"{prefix} {case_id}: source_evidence must be non-empty")
    else:
        for evidence_index, evidence_ref in enumerate(source_evidence):
            if not ref_exists(evidence_ref):
                add_error(errors, f"{prefix} {case_id}: source_evidence[{evidence_index}] does not exist: {evidence_ref}")
    account = contract.get("account")
    if not isinstance(account, dict):
        add_error(errors, f"{prefix} {case_id}: account must be a mapping")
    else:
        for key in ("state", "isolation", "reuse_allowed", "reset_strategy"):
            if key not in account or account.get(key) in (None, ""):
                add_error(errors, f"{prefix} {case_id}: account.{key} is required")
    entry = contract.get("entry")
    if not isinstance(entry, dict) or not entry.get("url"):
        add_error(errors, f"{prefix} {case_id}: entry.url is required")
    elif not as_list(entry.get("flow")):
        add_error(errors, f"{prefix} {case_id}: entry.flow must be non-empty")
    state_chain = as_list(contract.get("state_chain"))
    if not state_chain:
        add_error(errors, f"{prefix} {case_id}: state_chain must be non-empty")
    for state_index, state in enumerate(state_chain):
        if not isinstance(state, dict) or not state.get("state"):
            add_error(errors, f"{prefix} {case_id}: state_chain[{state_index}] missing state")
        elif not as_list(state.get("ready_when")):
            add_error(errors, f"{prefix} {case_id}: state_chain[{state_index}] missing ready_when")
    actions = as_list(contract.get("actions"))
    if not actions:
        add_error(errors, f"{prefix} {case_id}: actions must be non-empty")
    for action_index, action in enumerate(actions):
        if not isinstance(action, dict):
            add_error(errors, f"{prefix} {case_id}: actions[{action_index}] must be a mapping")
            continue
        for key in ("action_id", "action", "ready_when", "result"):
            if key not in action or action.get(key) in (None, "") or (isinstance(action.get(key), list) and not action.get(key)):
                add_error(errors, f"{prefix} {case_id}: actions[{action_index}] missing {key}")
        if action.get("action") in {"click", "fill", "upload", "touch", "dispatch"} and not action.get("button_ref"):
            add_error(errors, f"{prefix} {case_id}: actions[{action_index}] needs button_ref")
        if not action.get("driver"):
            add_error(errors, f"{prefix} {case_id}: actions[{action_index}] needs driver")
    capture = contract.get("event_capture")
    if not isinstance(capture, dict):
        add_error(errors, f"{prefix} {case_id}: event_capture must be a mapping")
    elif capture.get("enabled", True):
        for key in ("reset_before_action", "start_after", "stop_after", "expected"):
            if key not in capture or capture.get(key) in (None, "") or (isinstance(capture.get(key), list) and not capture.get(key)):
                add_error(errors, f"{prefix} {case_id}: event_capture.{key} is required when enabled")
        for expected_index, expected in enumerate(as_list(capture.get("expected"))):
            if not isinstance(expected, dict) or not expected.get("event"):
                add_error(errors, f"{prefix} {case_id}: event_capture.expected[{expected_index}] missing event")
            elif expected.get("send_count") != 1 or expected.get("debug_count") != 1:
                add_error(errors, f"{prefix} {case_id}: event_capture.expected[{expected_index}] must declare send_count=1 and debug_count=1")
    evidence = contract.get("evidence")
    if not isinstance(evidence, dict):
        add_error(errors, f"{prefix} {case_id}: evidence must be a mapping")
    else:
        evidence_refs = [ref for key in ("screenshots", "console", "dom") for ref in as_list(evidence.get(key))]
        if not evidence_refs:
            add_error(errors, f"{prefix} {case_id}: evidence must contain screenshot, console, or dom reference")
        for evidence_ref in evidence_refs:
            if not ref_exists(evidence_ref):
                add_error(errors, f"{prefix} {case_id}: evidence reference does not exist: {evidence_ref}")
    if contract.get("implementation_status") != "ready":
        add_error(errors, f"{prefix} {case_id}: implementation_status must be ready")


def validate(args: argparse.Namespace) -> int:
    handoff_path = resolve_repo_path(args.handoff)
    errors: list[str] = []
    if not handoff_path.exists():
        print(f"handoff not found: {handoff_path}", file=sys.stderr)
        return 2
    handoff = load_yaml(handoff_path)
    if not isinstance(handoff, dict):
        errors.append("handoff must be a mapping")
        handoff = {}
    for key in ("schema_version", "task_id", "status", "page_map_ref", "sync_ref", "exploration_report_ref", "contracts"):
        if key not in handoff:
            errors.append(f"handoff: missing {key}")
    status = handoff.get("status")
    if status not in STATUSES:
        errors.append(f"handoff.status={status!r} not in {sorted(STATUSES)}")
    page_map_ref = handoff.get("page_map_ref")
    if page_map_ref and not resolve_repo_path(str(page_map_ref)).exists():
        errors.append(f"handoff.page_map_ref does not exist: {page_map_ref}")
    for ref_key in ("sync_ref", "exploration_report_ref"):
        ref = handoff.get(ref_key)
        if ref and not resolve_repo_path(str(ref)).exists():
            errors.append(f"handoff.{ref_key} does not exist: {ref}")
    report_ref = handoff.get("exploration_report_ref")
    if report_ref and resolve_repo_path(str(report_ref)).exists():
        report_text = resolve_repo_path(str(report_ref)).read_text(encoding="utf-8")
        for heading in ("## 1. 任务概览", "## 2. 探索范围与覆盖", "## 3. 关键入口与状态", "## 4. Bug Candidate", "## 5. Gap / Skipped / Pending", "## 6. 自动化准备度", "## 7. 需要用户确认"):
            if heading not in report_text:
                errors.append(f"exploration_report missing heading: {heading}")
    contracts = handoff.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        errors.append("handoff.contracts must be a non-empty list")
        contracts = []
    seen: set[str] = set()
    for index, contract in enumerate(contracts, start=1):
        if not isinstance(contract, dict):
            errors.append(f"contracts[{index}] must be a mapping")
            continue
        case_id = contract.get("case_id")
        if case_id in seen:
            errors.append(f"duplicate contract case_id: {case_id}")
        seen.add(case_id)
        validate_contract(contract, index, errors)
    if status == "ready_for_case_design" and handoff.get("blocking_items"):
        errors.append("ready_for_case_design cannot have blocking_items")
    if args.cases:
        cases_path = resolve_repo_path(args.cases)
        if not cases_path.exists():
            errors.append(f"cases not found: {cases_path}")
        else:
            cases_meta = read_frontmatter(cases_path)
            if cases_meta.get("page_map") != page_map_ref:
                errors.append(f"page_map version mismatch: handoff={page_map_ref!r}, cases={cases_meta.get('page_map')!r}")
            handoff_ref = str(handoff_path.relative_to(ROOT)).replace("\\", "/")
            cases_handoff_ref = str(cases_meta.get("automation_handoff") or "").replace("\\", "/")
            if cases_handoff_ref not in {handoff_ref, str(handoff_path).replace("\\", "/"), ""}:
                errors.append(f"cases automation_handoff mismatch: expected {handoff_ref!r}, got {cases_meta.get('automation_handoff')!r}")
            if cases_handoff_ref == "":
                errors.append("cases frontmatter missing automation_handoff")
            ids = case_ids(cases_path)
            missing = sorted(ids - seen)
            extra = sorted(seen - ids)
            if missing:
                errors.append(f"cases missing handoff contracts: {', '.join(missing)}")
            if extra:
                errors.append(f"handoff has contracts not present in cases: {', '.join(extra)}")
            if status == "implementation_ready" and cases_meta.get("status") != "confirmed":
                errors.append(f"cases.status must be confirmed for implementation_ready, got {cases_meta.get('status')!r}")
    if status == "implementation_ready":
        if handoff.get("blocking_items"):
            errors.append("implementation_ready cannot have blocking_items")
        if handoff.get("unresolved_conflicts"):
            errors.append("implementation_ready cannot have unresolved_conflicts")
        if not args.cases:
            errors.append("implementation_ready requires --cases")
        sync_path = resolve_repo_path(str(handoff.get("sync_ref")))
        if sync_path.exists() and read_frontmatter(sync_path).get("status") != "confirmed":
            errors.append("sync.status must be confirmed before implementation_ready")
    if errors:
        print("Automation handoff validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Automation handoff validation passed: status={status}, contracts={len(contracts)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="validate exploration-to-code handoff")
    parser.add_argument("--handoff", required=True)
    parser.add_argument("--cases")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")
    return validate(args)


if __name__ == "__main__":
    raise SystemExit(main())

