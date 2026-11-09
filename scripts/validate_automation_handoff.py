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
# Contract 级实现状态：ready=可直接实现；known_bug=按需求期望断言但当前存在埋点缺陷；
# blocked_by_dependency=入口/依赖缺失，暂不可实现。
CONTRACT_STATUSES = {"ready", "known_bug", "blocked_by_dependency"}
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


def add_warning(warnings: list[str], message: str) -> None:
    warnings.append(message)


LOW_STABILITY_HINTS = (
    "nth-child", "nth-of-type", "position", "coordinate", "index=",
)


def check_locator_warnings(action: dict[str, Any], prefix: str, case_id: str, warnings: list[str]) -> None:
    """Non-blocking stability checks for action.locator."""
    locator = action.get("locator")
    aid = action.get("action_id")
    if not isinstance(locator, dict):
        if action.get("driver") in ("dispatchEvent", "JS") or action.get("action") == "set_value":
            add_warning(warnings, prefix + " " + case_id + ": action " + str(aid) + " has no locator block")
        return
    stability = str(locator.get("stability") or "").lower()
    if stability not in {"high", "medium", "low"}:
        add_warning(warnings, prefix + " " + case_id + ": action " + str(aid) + " locator.stability invalid: " + repr(locator.get("stability")))
        return
    if stability in {"low", "medium"} and not locator.get("fallback"):
        add_warning(warnings, prefix + " " + case_id + ": action " + str(aid) + " stability=" + stability + " but no fallback")
    primary = locator.get("primary")
    if isinstance(primary, dict):
        value = str(primary.get("value") or "")
        if any(hint in value for hint in LOW_STABILITY_HINTS) and stability != "low":
            add_warning(warnings, prefix + " " + case_id + ": action " + str(aid) + " primary locator looks order/position based but stability=" + stability)



def validate_contract(contract: dict[str, Any], index: int, errors: list[str], warnings: list[str]) -> None:
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
    implementation_status = contract.get("implementation_status")
    blocked_by_dependency = implementation_status == "blocked_by_dependency"
    entry = contract.get("entry")
    entry_url = entry.get("url") if isinstance(entry, dict) else None
    dependency_entry = isinstance(entry_url, str) and entry_url.startswith("dependency:")
    if not isinstance(entry, dict) or not entry_url:
        add_error(errors, f"{prefix} {case_id}: entry.url is required")
    elif not as_list(entry.get("flow")) and not dependency_entry:
        add_error(errors, f"{prefix} {case_id}: entry.flow must be non-empty")
    state_chain = as_list(contract.get("state_chain"))
    if not state_chain and not blocked_by_dependency:
        add_error(errors, f"{prefix} {case_id}: state_chain must be non-empty")
    for state_index, state in enumerate(state_chain):
        if not isinstance(state, dict) or not state.get("state"):
            add_error(errors, f"{prefix} {case_id}: state_chain[{state_index}] missing state")
        elif not as_list(state.get("ready_when")):
            add_error(errors, f"{prefix} {case_id}: state_chain[{state_index}] missing ready_when")
    actions = as_list(contract.get("actions"))
    if not actions and not blocked_by_dependency:
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
        check_locator_warnings(action, prefix, case_id, warnings)
    confidence = contract.get("confidence")
    if confidence not in ("high", "medium", "low"):
        add_warning(warnings, prefix + " " + str(case_id) + ": contract.confidence missing or invalid")
    if any(isinstance(a, dict) and a.get("action") == "set_value" for a in actions):
        if not contract.get("not_visible_when") and not any(isinstance(a, dict) and a.get("not_visible_when") for a in actions):
            add_warning(warnings, prefix + " " + str(case_id) + ": has set_value actions but no not_visible_when / absent-state rule")
    if not contract.get("failure_routing"):
        add_warning(warnings, prefix + " " + str(case_id) + ": contract.failure_routing missing")

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
    if implementation_status not in CONTRACT_STATUSES:
        add_error(
            errors,
            f"{prefix} {case_id}: implementation_status={implementation_status!r} "
            f"not in {sorted(CONTRACT_STATUSES)}",
        )
    elif implementation_status == "known_bug":
        bug = contract.get("known_bug")
        if not isinstance(bug, dict):
            add_error(errors, f"{prefix} {case_id}: known_bug must be a mapping when implementation_status=known_bug")
        else:
            for key in ("id", "expected_event", "actual_event", "evidence"):
                if not bug.get(key):
                    add_error(errors, f"{prefix} {case_id}: known_bug.{key} is required")
    elif implementation_status == "blocked_by_dependency":
        dependency = contract.get("dependency")
        if not isinstance(dependency, dict):
            add_error(
                errors,
                f"{prefix} {case_id}: dependency must be a mapping when implementation_status=blocked_by_dependency",
            )
        else:
            for key in ("id", "reason", "owner"):
                if not dependency.get(key):
                    add_error(errors, f"{prefix} {case_id}: dependency.{key} is required")


def validate(args: argparse.Namespace) -> int:
    handoff_path = resolve_repo_path(args.handoff)
    errors: list[str] = []
    warnings: list[str] = []
    if not handoff_path.exists():
        print(f"handoff not found: {handoff_path}", file=sys.stderr)
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
    report_text = ""
    if report_ref and resolve_repo_path(str(report_ref)).exists():
        report_text = resolve_repo_path(str(report_ref)).read_text(encoding="utf-8")
        required_report_headings = (
            "## 1. 任务概览",
            "## 2. 探索范围与覆盖",
            "## 3. 关键入口与状态",
            "## 4. Bug Candidate",
            "## 5. Gap / Skipped / Pending",
            "## 6. 自动化准备度",
            "## 7. 需要用户确认",
            "## 8. 已执行用例（按用例名标注）",
            "## 9. Bug Candidate 明细（可展开查看截图）",
            "## 10. 未执行用例（按用例名标注）",
        )
        for heading in required_report_headings:
            if heading not in report_text:
                errors.append(f"exploration_report missing heading: {heading}")
        if "![" in report_text:
            errors.append("exploration_report must not use Markdown image syntax; put screenshots in collapsed HTML <details><img> blocks")
        executed_parts = report_text.split("## 8. 已执行用例（按用例名标注）", 1)
        executed_text = ""
        if len(executed_parts) == 2:
            executed_text = executed_parts[1].split("## 9. Bug Candidate 明细（可展开查看截图）", 1)[0]
        if "AC-" not in executed_text and "无" not in executed_text:
            errors.append("exploration_report section 8 must list executed cases by AC/name")
        unexecuted_parts = report_text.split("## 10. 未执行用例（按用例名标注）", 1)
        unexecuted_text = unexecuted_parts[1] if len(unexecuted_parts) == 2 else ""
        if "### 10.1 Gap" not in unexecuted_text or "### 10.2 Skipped" not in unexecuted_text:
            errors.append("exploration_report section 10 must split Gap and Skipped subheadings")
        if "AC-" not in unexecuted_text and "无" not in unexecuted_text:
            errors.append("exploration_report section 10 must list unexecuted cases by AC/name")
    contracts = handoff.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        errors.append("handoff.contracts must be a non-empty list")
        contracts = []
    known_bug_contracts = [
        contract for contract in contracts
        if isinstance(contract, dict) and contract.get("implementation_status") == "known_bug"
    ]
    if known_bug_contracts and report_text:
        bug_section = report_text.split("## 9. Bug Candidate 明细（可展开查看截图）", 1)
        bug_section_text = bug_section[1] if len(bug_section) == 2 else ""
        if not bug_section_text:
            errors.append("exploration_report is missing Bug Candidate details section content")
        for contract in known_bug_contracts:
            case_id = contract.get("case_id", "<unknown>")
            if case_id not in executed_text:
                errors.append(f"exploration_report section 8 missing executed bug case: {case_id}")
            if case_id not in bug_section_text:
                errors.append(f"exploration_report Bug Candidate details missing {case_id}")
            if "<details>" not in bug_section_text or "<img src=" not in bug_section_text:
                errors.append("exploration_report Bug Candidate details must use collapsed HTML <details><img> screenshot blocks")
                break
    seen: set[str] = set()
    for index, contract in enumerate(contracts, start=1):
        if not isinstance(contract, dict):
            errors.append(f"contracts[{index}] must be a mapping")
            continue
        case_id = contract.get("case_id")
        if case_id in seen:
            errors.append(f"duplicate contract case_id: {case_id}")
        seen.add(case_id)
        validate_contract(contract, index, errors, warnings)
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
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1
    if warnings:
        for warning in warnings:
            print(f"WARN: {warning}")
    if warnings and getattr(args, "strict", False):
        print(f"Automation handoff validation failed (strict): {len(warnings)} warning(s)")
        return 1
    print(f"Automation handoff validation passed: status={status}, contracts={len(contracts)}, warnings={len(warnings)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="validate exploration-to-code handoff")
    parser.add_argument("--handoff", required=True)
    parser.add_argument("--cases")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")
    return validate(args)


if __name__ == "__main__":
    raise SystemExit(main())





