#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit stable case_id coverage across collected tests (read-only).

Writes a temporary conftest into a scratch directory and runs pytest collection
as a subprocess, so it behaves like normal collection and never launches a
browser or touches the product site.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PLUGIN = r'''
import inspect
import json
import os
import sys

sys.path.insert(0, os.environ["CASE_ID_REPO_ROOT"])
sys.path.insert(0, os.path.join(os.environ["CASE_ID_REPO_ROOT"], "scripts"))
import regression_governance

DYNAMIC_A = 'allure.dynamic.label("case_id"'
DYNAMIC_B = "allure.dynamic.label('case_id'"


def _sets_dynamic_case_id(item):
    obj = getattr(item, "obj", None)
    targets = [obj, getattr(item, "parent", None)]
    for target in targets:
        inner = getattr(target, "obj", target)
        if inner is None:
            continue
        try:
            src = inspect.getsource(inner)
        except Exception:
            continue
        if DYNAMIC_A in src or DYNAMIC_B in src:
            return True
    return False


def pytest_collection_modifyitems(session, config, items):
    rows = []
    for item in items:
        cid = regression_governance._case_id(item)
        static = not cid.startswith("MISSING_CASE_ID:")
        title = regression_governance._title(item)
        dynamic = (not static) and _sets_dynamic_case_id(item)
        # Title-derivable: a strict case_id can be extracted from the static title.
        derived = ""
        if not static and not dynamic:
            try:
                from case_id_rules import case_id_from_title
                derived = case_id_from_title(title, item.nodeid)
            except Exception:
                derived = ""
        rows.append({
            "nodeid": item.nodeid,
            "case_id": cid,
            "title": title,
            "resolved_static": static,
            "dynamic_runtime": dynamic,
            "title_derivable": bool(derived),
            "derived_case_id": derived,
        })
    with open(os.environ["CASE_ID_AUDIT_OUT"], "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)
'''


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit case_id coverage")
    parser.add_argument("target", nargs="?", default="tests")
    parser.add_argument("--json-out", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    scratch = Path(tempfile.mkdtemp(prefix="case-id-audit-"))
    rows_path = scratch / "rows.json"
    env = dict(os.environ)
    env["CASE_ID_REPO_ROOT"] = str(ROOT)
    env["CASE_ID_AUDIT_OUT"] = str(rows_path)
    env["PYTHONPATH"] = str(scratch) + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    (scratch / "case_id_audit_plugin.py").write_text(PLUGIN, encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(ROOT / args.target), "-q", "--collect-only",
             "-p", "no:cacheprovider", "-p", "case_id_audit_plugin"],
            cwd=str(scratch), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if not rows_path.exists() or not rows_path.read_text(encoding="utf-8").strip():
            print(proc.stdout[-3000:])
            print(proc.stderr[-3000:], file=sys.stderr)
            return 2
        rows = json.loads(rows_path.read_text(encoding="utf-8"))
    finally:
        # Windows may still hold the temp file briefly; best-effort cleanup.
        try:
            shutil.rmtree(scratch, ignore_errors=True)
        except Exception:
            pass

    static_rows = [r for r in rows if r.get("resolved_static")]
    dynamic_rows = [r for r in rows if r.get("dynamic_runtime")]
    title_rows = [r for r in rows if r.get("title_derivable")]
    missing = [
        r for r in rows
        if not r.get("resolved_static")
        and not r.get("dynamic_runtime")
        and not r.get("title_derivable")
    ]
    unique = {r["case_id"] for r in static_rows}
    print(
        f"collected={len(rows)} "
        f"label_marker={len(static_rows)} "
        f"dynamic_runtime={len(dynamic_rows)} "
        f"title_derivable={len(title_rows)} "
        f"missing={len(missing)}"
    )
    print(
        "note: dynamic_runtime / title_derivable cases resolve at run time "
        "(Allure label or strict title extraction); missing = true debt."
    )
    if missing:
        print("\nMISSING_CASE_ID examples (true debt):")
        for row in missing[:25]:
            print(f"  - {row['nodeid']} | title={row['title']!r}")
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "collected": len(rows),
                    "label_marker": len(static_rows),
                    "dynamic_runtime": len(dynamic_rows),
                    "title_derivable": len(title_rows),
                    "missing": missing,
                    "dynamic_nodeids": [r["nodeid"] for r in dynamic_rows],
                },
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
