#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quarantine registry manager.

Commands:
  list                 show all entries with days-to-expiry
  add                  register a case (requires owner + reason + evidence)
  extend               push expiry out (records history)
  release              deactivate an entry (kept for audit, not deleted)
  audit                flag entries that are expired or past the upgrade threshold

Rules enforced:
  * required fields: case_id / reason / owner / opened_at / expires_at / evidence
  * entries are never deleted, only deactivated (status=released)
  * an entry past upgrade_after_consecutive_runs is flagged for escalation
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "artifacts" / "regression_quarantine.yaml"
REQUIRED = ("case_id", "reason", "owner", "opened_at", "expires_at", "evidence")


def _today() -> date:
    return datetime.now(timezone.utc).astimezone().date()


def _registry_path() -> Path:
    global REGISTRY
    return REGISTRY


def _load() -> dict[str, Any]:
    if not _registry_path().exists():
        return {"schema_version": "1.0", "quarantine": []}
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"invalid registry: {REGISTRY}")
    data.setdefault("quarantine", [])
    return data


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = _today().isoformat()
    _registry_path().write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _find(data: dict[str, Any], case_id: str) -> dict[str, Any] | None:
    for item in data.get("quarantine", []):
        if str(item.get("case_id")) == case_id:
            return item
    return None


def _status(item: dict[str, Any]) -> str:
    return str(item.get("status") or "active").lower()


def cmd_list(args) -> int:
    data = _load()
    items = data.get("quarantine", [])
    if not items:
        print("[quarantine] empty")
        return 0
    today = _today()
    for item in items:
        cid = item.get("case_id")
        st = _status(item)
        expires = str(item.get("expires_at") or "")
        days = "?"
        try:
            days = (date.fromisoformat(expires[:10]) - today).days
        except ValueError:
            pass
        flag = ""
        if st in {"active", "quarantined"} and isinstance(days, int) and days < 0:
            flag = "  <-- EXPIRED"
        print(f"  {cid:24} {st:10} expires={expires} days_left={days}{flag}")
    return 0


def cmd_add(args) -> int:
    data = _load()
    if _find(data, args.case_id):
        print(f"[quarantine] already registered: {args.case_id}", file=sys.stderr)
        return 2
    opened = args.opened or _today().isoformat()
    expires = args.expires or (_today() + timedelta(days=args.days)).isoformat()
    entry = {
        "case_id": args.case_id,
        "reason": args.reason,
        "owner": args.owner,
        "opened_at": opened,
        "expires_at": expires,
        "evidence": args.evidence,
        "status": "active",
        "consecutive_runs": 0,
    }
    data["quarantine"].append(entry)
    _save(data)
    print(f"[quarantine] added {args.case_id} (expires {expires})")
    return 0


def cmd_extend(args) -> int:
    data = _load()
    item = _find(data, args.case_id)
    if not item:
        print(f"[quarantine] not found: {args.case_id}", file=sys.stderr)
        return 2
    base = _today()
    try:
        base = max(base, date.fromisoformat(str(item.get("expires_at"))[:10]))
    except ValueError:
        pass
    item["expires_at"] = (base + timedelta(days=args.days)).isoformat()
    item.setdefault("history", []).append({
        "at": _today().isoformat(),
        "action": "extend",
        "note": args.note or "",
    })
    _save(data)
    print(f"[quarantine] extended {args.case_id} -> {item['expires_at']}")
    return 0


def cmd_release(args) -> int:
    data = _load()
    item = _find(data, args.case_id)
    if not item:
        print(f"[quarantine] not found: {args.case_id}", file=sys.stderr)
        return 2
    item["status"] = "released"
    item["released_at"] = _today().isoformat()
    item["release_reason"] = args.reason or ""
    _save(data)
    print(f"[quarantine] released {args.case_id}")
    return 0


def cmd_audit(args) -> int:
    data = _load()
    policy = data.get("policy") or {}
    threshold = int(policy.get("upgrade_after_consecutive_runs") or 3)
    today = _today()
    problems = []
    for item in data.get("quarantine", []):
        if _status(item) not in {"active", "quarantined"}:
            continue
        cid = item.get("case_id")
        missing = [f for f in REQUIRED if not item.get(f)]
        if missing:
            problems.append(f"{cid}: missing fields {missing}")
        expires = str(item.get("expires_at") or "")
        try:
            if date.fromisoformat(expires[:10]) < today:
                problems.append(f"{cid}: expired on {expires}")
        except ValueError:
            problems.append(f"{cid}: invalid expires_at {expires!r}")
        runs = int(item.get("consecutive_runs") or 0)
        if runs >= threshold:
            problems.append(f"{cid}: {runs} consecutive runs >= threshold {threshold}; escalate")
    if not problems:
        print("[quarantine] audit clean")
        return 0
    for p in problems:
        print(f"  - {p}")
    return 1


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quarantine registry manager")
    parser.add_argument("--registry", default=str(REGISTRY), help="path to quarantine registry yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")
    sub.add_parser("audit")

    p_add = sub.add_parser("add")
    p_add.add_argument("case_id")
    p_add.add_argument("--reason", required=True)
    p_add.add_argument("--owner", required=True)
    p_add.add_argument("--evidence", required=True)
    p_add.add_argument("--opened", default=None)
    p_add.add_argument("--expires", default=None)
    p_add.add_argument("--days", type=int, default=14)

    p_ext = sub.add_parser("extend")
    p_ext.add_argument("case_id")
    p_ext.add_argument("--days", type=int, default=7)
    p_ext.add_argument("--note", default=None)

    p_rel = sub.add_parser("release")
    p_rel.add_argument("case_id")
    p_rel.add_argument("--reason", default=None)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = _parse_args(argv)
    global REGISTRY
    candidate = Path(args.registry)
    REGISTRY = candidate if candidate.is_absolute() else ROOT / candidate
    return {
        "list": cmd_list,
        "add": cmd_add,
        "extend": cmd_extend,
        "release": cmd_release,
        "audit": cmd_audit,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())