#!/usr/bin/env python3
"""轻量项目业务知识库工具。

默认只读取 knowledge/index.yaml；--details 仅读取命中的知识切片。
用途：校验、重建索引、窄范围检索和记录检索账本。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = ROOT / "knowledge"
INDEX_PATH = KNOWLEDGE_ROOT / "index.yaml"

REQUIRED_FIELDS = {
    "schema_version",
    "knowledge_id",
    "knowledge_type",
    "title",
    "subject_key",
    "status",
    "priority",
    "confidence",
    "summary",
    "rule",
    "source_of_truth",
    "source_refs",
    "evidence",
    "retrieval_tags",
    "last_verified_at",
    "created_at",
    "updated_at",
}
ENUMS = {
    "knowledge_type": {
        "business_rule",
        "legacy_entry",
        "state_transition",
        "validation_rule",
        "permission_rule",
        "data_constraint",
        "historical_pitfall",
        "environment_behavior",
        "ui_residue",
        "technical_test_rule",
    },
    "status": {"active", "needs_verification", "conflict", "superseded", "retired", "ui_residue"},
    "priority": {"P0", "P1", "P2", "P3"},
    "confidence": {"high", "medium", "low"},
}
DEFAULT_STATUS = {"active", "needs_verification"}
PURPOSE_TYPES = {
    "entry": {"legacy_entry", "ui_residue"},
    "rule": {"business_rule", "state_transition", "data_constraint"},
    "validation": {"validation_rule", "data_constraint"},
    "permission": {"permission_rule"},
    "pitfall": {"historical_pitfall", "environment_behavior", "technical_test_rule"},
    "conflict": set(),
}
SECRET_KEY_PARTS = {
    "password",
    "cookie",
    "token",
    "secret",
    "api_key",
    "access_key",
    "verification_code",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def dump_yaml(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)


def iter_slice_files() -> Iterable[Path]:
    shared = KNOWLEDGE_ROOT / "shared.yaml"
    if shared.exists():
        yield shared
    modules = KNOWLEDGE_ROOT / "modules"
    if modules.exists():
        yield from sorted(modules.rglob("*.yaml"))


def extract_slices(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("knowledge_slices"), list):
        return [x for x in data["knowledge_slices"] if isinstance(x, dict)]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def relative_to_root(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def relative_to_knowledge(path: Path) -> str:
    return path.relative_to(KNOWLEDGE_ROOT).as_posix()


def flatten_strings(value: Any, key: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            yield from flatten_strings(child_value, f"{key}.{child_key}" if key else str(child_key))
    elif isinstance(value, list):
        for child in value:
            yield from flatten_strings(child, key)
    elif value is not None:
        yield key, str(value)


def check_privacy(slice_data: dict[str, Any], location: str, errors: list[str]) -> None:
    for key, value in flatten_strings(slice_data):
        lower_key = key.casefold()
        if any(part in lower_key for part in SECRET_KEY_PARTS) and value.strip():
            errors.append(f"{location}: forbidden sensitive field '{key}'")


def validate_ref_exists(ref: str) -> bool:
    value = ref.strip()
    if not value or value.startswith(("http://", "https://", "user_decision:", "task:", "artifact:")):
        return True
    # Strip a YAML-style anchor such as file.md#section and allow documented globs/directories.
    path_part = value.split("#", 1)[0].strip()
    if "<" in path_part or "*" in path_part:
        return True
    return (ROOT / path_part).exists() or (KNOWLEDGE_ROOT / path_part).exists()


def validate_slice(slice_data: dict[str, Any], location: str, errors: list[str]) -> None:
    missing = sorted(REQUIRED_FIELDS - slice_data.keys())
    if missing:
        errors.append(f"{location}: missing required fields: {', '.join(missing)}")
    for field, allowed in ENUMS.items():
        value = slice_data.get(field)
        if value not in allowed:
            errors.append(f"{location}: {field}={value!r} not in {sorted(allowed)}")
    rule = slice_data.get("rule")
    if not isinstance(rule, dict) or not all(isinstance(rule.get(k), list) for k in ("given", "when", "then")):
        errors.append(f"{location}: rule must contain list fields given/when/then")
    source_of_truth = slice_data.get("source_of_truth")
    if not isinstance(source_of_truth, str) or not source_of_truth.strip():
        errors.append(f"{location}: source_of_truth must be a non-empty string")
    source_refs = slice_data.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        errors.append(f"{location}: source_refs must be a non-empty list")
    else:
        for ref_number, ref_item in enumerate(source_refs, start=1):
            if not isinstance(ref_item, dict) or not str(ref_item.get("ref", "")).strip():
                errors.append(f"{location}: source_refs[{ref_number}] must contain a non-empty ref")
            elif not validate_ref_exists(str(ref_item.get("ref"))):
                errors.append(f"{location}: source_refs[{ref_number}] does not exist: {ref_item.get('ref')}")
    evidence = slice_data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{location}: evidence must be a non-empty list")
    else:
        for evidence_number, evidence_item in enumerate(evidence, start=1):
            if not isinstance(evidence_item, dict):
                errors.append(f"{location}: evidence[{evidence_number}] must be a mapping")
                continue
            for evidence_key in ("kind", "ref", "verified_at", "result"):
                if not str(evidence_item.get(evidence_key, "")).strip():
                    errors.append(f"{location}: evidence[{evidence_number}] missing {evidence_key}")
            if str(evidence_item.get("ref", "")).strip() and not validate_ref_exists(str(evidence_item.get("ref"))):
                errors.append(f"{location}: evidence[{evidence_number}] does not exist: {evidence_item.get('ref')}")
    if slice_data.get("status") == "active" and not str(slice_data.get("last_verified_at", "")).strip():
        errors.append(f"{location}: active slice requires last_verified_at")
    tags = slice_data.get("retrieval_tags")
    if not isinstance(tags, dict):
        errors.append(f"{location}: retrieval_tags must be a mapping")
    check_privacy(slice_data, location, errors)


def validate_index(index_data: dict[str, Any], all_ids: set[str], errors: list[str]) -> None:
    entries = index_data.get("knowledge_index")
    if not isinstance(entries, list):
        errors.append("knowledge/index.yaml: knowledge_index must be a list")
        return
    seen: set[str] = set()
    for number, entry in enumerate(entries, start=1):
        location = f"knowledge/index.yaml[{number}]"
        if not isinstance(entry, dict):
            errors.append(f"{location}: entry must be a mapping")
            continue
        knowledge_id = entry.get("knowledge_id")
        if not knowledge_id:
            errors.append(f"{location}: missing knowledge_id")
        elif knowledge_id in seen:
            errors.append(f"{location}: duplicate knowledge_id {knowledge_id}")
        else:
            seen.add(knowledge_id)
        if knowledge_id not in all_ids:
            errors.append(f"{location}: knowledge_id {knowledge_id} is not present in a module/shared slice")
        file_ref = entry.get("file")
        if not file_ref:
            errors.append(f"{location}: missing file")
        elif not (KNOWLEDGE_ROOT / file_ref).exists():
            errors.append(f"{location}: file does not exist: knowledge/{file_ref}")
    expected = all_ids
    if seen != expected:
        missing = sorted(expected - seen)
        extra = sorted(seen - expected)
        if missing:
            errors.append(f"knowledge/index.yaml: missing ids: {', '.join(missing)}")
        if extra:
            errors.append(f"knowledge/index.yaml: stale ids: {', '.join(extra)}")


def validate() -> int:
    errors: list[str] = []
    all_slices: dict[str, tuple[Path, dict[str, Any]]] = {}
    subject_slices: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path in iter_slice_files():
        try:
            data = load_yaml(path)
        except Exception as exc:  # pragma: no cover - defensive CLI path
            errors.append(f"{relative_to_root(path)}: YAML load failed: {exc}")
            continue
        slices = extract_slices(data)
        if not slices:
            errors.append(f"{relative_to_root(path)}: no knowledge_slices list")
        for number, slice_data in enumerate(slices, start=1):
            location = f"{relative_to_root(path)}[{number}]"
            validate_slice(slice_data, location, errors)
            knowledge_id = slice_data.get("knowledge_id")
            if knowledge_id:
                if knowledge_id in all_slices:
                    errors.append(f"{location}: duplicate knowledge_id {knowledge_id}; previous={relative_to_root(all_slices[knowledge_id][0])}")
                all_slices[knowledge_id] = (path, slice_data)
            subject_key = slice_data.get("subject_key")
            if subject_key:
                subject_slices.setdefault(str(subject_key), []).append((path, slice_data))
    for subject_key, items in subject_slices.items():
        live_items = [(path, item) for path, item in items if item.get("status") in {"active", "needs_verification"}]
        if len(live_items) > 1:
            ids = ", ".join(str(item.get("knowledge_id")) for _, item in live_items)
            errors.append(f"duplicate live subject_key {subject_key}: {ids}; use supersedes/retired for replacement")
    if not INDEX_PATH.exists():
        errors.append("knowledge/index.yaml: file does not exist")
    else:
        try:
            validate_index(load_yaml(INDEX_PATH), set(all_slices), errors)
        except Exception as exc:  # pragma: no cover - defensive CLI path
            errors.append(f"knowledge/index.yaml: YAML load failed: {exc}")
    if errors:
        print("Knowledge validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Knowledge validation passed: {len(all_slices)} slices")
    return 0


def build_index() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in iter_slice_files():
        data = load_yaml(path)
        for slice_data in extract_slices(data):
            tags = slice_data.get("retrieval_tags") or {}
            flat_tags = sorted({str(item) for values in tags.values() if isinstance(values, list) for item in values})
            entries.append(
                {
                    "knowledge_id": slice_data.get("knowledge_id"),
                    "file": relative_to_knowledge(path),
                    "subject_key": slice_data.get("subject_key"),
                    "knowledge_type": slice_data.get("knowledge_type"),
                    "status": slice_data.get("status"),
                    "priority": slice_data.get("priority"),
                    "confidence": slice_data.get("confidence"),
                    "source_of_truth": slice_data.get("source_of_truth"),
                    "last_verified_at": slice_data.get("last_verified_at"),
                    "title": slice_data.get("title"),
                    "summary": slice_data.get("summary"),
                    "tags": flat_tags,
                }
            )
    entries.sort(key=lambda x: (x.get("subject_key") or "", x.get("knowledge_id") or ""))
    return {
        "index_schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "knowledge_index": entries,
    }


def rebuild_index() -> int:
    data = build_index()
    dump_yaml(data, INDEX_PATH)
    print(f"Rebuilt {INDEX_PATH}: {len(data['knowledge_index'])} slices")
    return 0


def normalize(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value.casefold()).strip()


def index_entries() -> list[dict[str, Any]]:
    data = load_yaml(INDEX_PATH)
    entries = data.get("knowledge_index") if isinstance(data, dict) else None
    return entries if isinstance(entries, list) else []


def candidate_text(entry: dict[str, Any]) -> str:
    fields = [
        entry.get("knowledge_id"),
        entry.get("subject_key"),
        entry.get("knowledge_type"),
        entry.get("title"),
        entry.get("summary"),
        *(entry.get("tags") or []),
    ]
    return normalize(" ".join(str(x) for x in fields if x))


def query_tokens(raw: str) -> list[str]:
    return [token for token in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+", normalize(raw)) if token]


def score_entry(entry: dict[str, Any], args: argparse.Namespace) -> tuple[int, list[str]]:
    text = candidate_text(entry)
    score = 0
    reasons: list[str] = []
    filters = {
        "module": args.module,
        "page": args.page,
        "feature": args.feature,
        "entry": args.entry,
        "state": args.state,
        "action": args.action,
        "account": args.account_state,
        "environment": args.environment,
        "platform": args.platform,
        "error": args.error,
    }
    for label, raw in filters.items():
        value = normalize(raw)
        if not value:
            continue
        if value in text:
            score += 8 if label in {"module", "page", "feature", "entry"} else 5
            reasons.append(label)
        else:
            return 0, []
    if args.query:
        tokens = query_tokens(args.query)
        matched = [token for token in tokens if token in text]
        if not matched:
            return 0, []
        score += 5 * len(matched)
        reasons.append("query:" + ",".join(matched))
    if args.purpose:
        types = PURPOSE_TYPES[args.purpose]
        if types and entry.get("knowledge_type") not in types:
            return 0, []
        if args.purpose == "conflict" and entry.get("status") != "conflict":
            return 0, []
        score += 3
        reasons.append(f"purpose:{args.purpose}")
    priority_weight = {"P0": 4, "P1": 3, "P2": 2, "P3": 1}
    confidence_weight = {"high": 3, "medium": 2, "low": 1}
    score += priority_weight.get(entry.get("priority"), 0)
    score += confidence_weight.get(entry.get("confidence"), 0)
    return score, reasons


def load_details(entry: dict[str, Any]) -> dict[str, Any] | None:
    path = KNOWLEDGE_ROOT / str(entry["file"])
    if not path.exists():
        return None
    data = load_yaml(path)
    for slice_data in extract_slices(data):
        if slice_data.get("knowledge_id") == entry.get("knowledge_id"):
            return slice_data
    return None


def append_ledger(path_value: str | None, args: argparse.Namespace, results: list[dict[str, Any]], hit_status: str) -> None:
    if not path_value:
        return
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    current: list[Any] = []
    if path.exists():
        loaded = load_yaml(path)
        if isinstance(loaded, list):
            current = loaded
    fields = [args.mode, args.module, args.page, args.feature, args.entry, args.state, args.action, args.account_state, args.environment, args.platform, args.error, args.query, args.purpose]
    query_key = "|".join(normalize(x) or "none" for x in fields)
    current.append(
        {
            "query_key": query_key,
            "mode": args.mode,
            "hit_status": hit_status,
            "result_ids": [x.get("knowledge_id") for x in results],
            "retrieved_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        }
    )
    dump_yaml(current, path)


def search(args: argparse.Namespace) -> int:
    max_by_mode = {"init": 5, "runtime": 4, "exception": 3}
    max_limit = max_by_mode[args.mode]
    if args.limit < 1 or args.limit > max_limit:
        print(f"--limit must be between 1 and {max_limit} for mode={args.mode}", file=sys.stderr)
        return 2
    if not any([args.query, args.module, args.page, args.feature, args.entry, args.state, args.action, args.account_state, args.environment, args.platform, args.error]):
        print("search requires at least one scope field or --query", file=sys.stderr)
        return 2
    exclude = {x.strip() for x in (args.exclude_id or []) if x.strip()}
    allowed_status = set(args.status or DEFAULT_STATUS)
    scored: list[tuple[int, dict[str, Any], list[str]]] = []
    for entry in index_entries():
        if entry.get("knowledge_id") in exclude:
            continue
        if entry.get("status") not in allowed_status:
            continue
        score, reasons = score_entry(entry, args)
        if score:
            scored.append((score, entry, reasons))
    scored.sort(key=lambda x: (-x[0], {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(x[1].get("priority"), 9), x[1].get("knowledge_id", "")))
    results: list[dict[str, Any]] = []
    for score, entry, reasons in scored[: args.limit]:
        item = {
            "knowledge_id": entry.get("knowledge_id"),
            "file": entry.get("file"),
            "title": entry.get("title"),
            "summary": entry.get("summary"),
            "status": entry.get("status"),
            "priority": entry.get("priority"),
            "confidence": entry.get("confidence"),
            "source_of_truth": entry.get("source_of_truth"),
            "last_verified_at": entry.get("last_verified_at"),
            "relevance_score": score,
            "match_reasons": reasons,
            "use_as": use_as(entry),
        }
        if args.details:
            details = load_details(entry)
            if details is not None:
                item["rule"] = details.get("rule")
                item["source_refs"] = details.get("source_refs")
                item["retrieval_tags"] = details.get("retrieval_tags")
        results.append(item)
    hit_status = "hit_exact" if results else "no_hit"
    append_ledger(args.ledger, args, results, hit_status)
    output = {"mode": args.mode, "hit_status": hit_status, "hit_count": len(results), "results": results}
    if args.format == "json":
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(output, allow_unicode=True, sort_keys=False))
    return 0


def use_as(entry: dict[str, Any]) -> str:
    mapping = {
        "legacy_entry": "entry_candidate",
        "ui_residue": "do_not_assert",
        "business_rule": "rule_candidate",
        "state_transition": "rule_candidate",
        "validation_rule": "expected_candidate",
        "permission_rule": "expected_candidate",
        "data_constraint": "expected_candidate",
        "historical_pitfall": "retry_hint",
        "environment_behavior": "retry_hint",
        "technical_test_rule": "implementation_hint",
    }
    return mapping.get(str(entry.get("knowledge_type")), "verification_required")



def add_candidate(args: argparse.Namespace) -> int:
    pending_path = KNOWLEDGE_ROOT / "candidates" / "pending.yaml"
    data = load_yaml(pending_path) if pending_path.exists() else {"schema_version": "1.0", "candidates": []}
    candidates = data.get("candidates") if isinstance(data, dict) else None
    if not isinstance(candidates, list):
        candidates = []
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    candidate_id = args.candidate_id or "KC-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    item = {
        "candidate_id": candidate_id,
        "knowledge_type": args.knowledge_type,
        "title": args.title,
        "subject_key": args.subject_key,
        "summary": args.summary,
        "status": "needs_verification",
        "suggested_use_as": args.suggested_use_as,
        "repeat_count": args.repeat_count,
        "source_refs": [{"ref": ref, "type": "task_artifact"} for ref in args.source_ref],
        "evidence": args.evidence,
        "created_at": now,
        "updated_at": now,
    }
    candidates.append(item)
    data["schema_version"] = "1.0"
    data["candidates"] = candidates
    dump_yaml(data, pending_path)
    print(f"Added candidate {candidate_id} to {pending_path}")
    return 0

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="项目业务知识库检索与校验工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="校验知识切片、索引和敏感字段")
    sub.add_parser("rebuild-index", help="从 shared.yaml 和 modules/ 重建 index.yaml")

    candidate_parser = sub.add_parser("candidate-add", help="将一次任务经验写入待确认候选，不直接进入 active")
    candidate_parser.add_argument("--candidate-id")
    candidate_parser.add_argument("--knowledge-type", required=True, choices=sorted(ENUMS["knowledge_type"]))
    candidate_parser.add_argument("--title", required=True)
    candidate_parser.add_argument("--subject-key", required=True)
    candidate_parser.add_argument("--summary", required=True)
    candidate_parser.add_argument("--source-ref", action="append", required=True)
    candidate_parser.add_argument("--evidence", action="append", required=True)
    candidate_parser.add_argument("--repeat-count", type=int, default=1)
    candidate_parser.add_argument("--suggested-use-as", default="verification_required", choices=["entry_candidate", "rule_candidate", "expected_candidate", "retry_hint", "verification_required"])

    search_parser = sub.add_parser("search", help="按当前任务范围窄检索知识库")
    search_parser.add_argument("--mode", choices=["init", "runtime", "exception"], default="init")
    search_parser.add_argument("--query")
    search_parser.add_argument("--module")
    search_parser.add_argument("--page")
    search_parser.add_argument("--feature")
    search_parser.add_argument("--entry")
    search_parser.add_argument("--state")
    search_parser.add_argument("--action")
    search_parser.add_argument("--account-state", dest="account_state")
    search_parser.add_argument("--environment")
    search_parser.add_argument("--platform")
    search_parser.add_argument("--error")
    search_parser.add_argument("--purpose", choices=sorted(PURPOSE_TYPES))
    search_parser.add_argument("--status", action="append", choices=sorted(ENUMS["status"]))
    search_parser.add_argument("--exclude-id", action="append")
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--details", action="store_true")
    search_parser.add_argument("--ledger")
    search_parser.add_argument("--format", choices=["yaml", "json"], default="yaml")
    return parser.parse_args()


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure) and not stream.__class__.__module__.startswith("_pytest"):
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    configure_output()
    args = parse_args()
    if args.command == "validate":
        return validate()
    if args.command == "rebuild-index":
        return rebuild_index()
    if args.command == "candidate-add":
        return add_candidate(args)
    if args.command == "search":
        return search(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

