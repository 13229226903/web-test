#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate skills/*/SKILL.md against the internal skill format standard.

Checks (see skills/README.md):
  1. frontmatter exists with non-empty name + description
  2. directory name == frontmatter name
  3. required sections exist
  4. canonical sections appear in the expected relative order
  5. referenced runtime/artifact paths exist

Exit code: 0 = pass, 1 = failures found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

REQUIRED = [
    "职责",
    "触发",
    "输入契约",
    "输出契约",
    "红线",
    "上下游",
    "progress",
    "业务知识库使用",
]

ORDER = [
    "职责",
    "触发",
    "输入契约",
    "输出契约",
    "前置检查",
    "工作流",
    "Gate 与判定",
    "失败分类",
    "红线",
    "循环约束",
    "上下游",
    "progress",
    "业务知识库使用",
]

REF_PATTERN = re.compile(r"\x60(artifacts/[^\x60]+|scripts/[^\x60]+|PROJECT\.md|rule\.md|helpers/[^\x60]+)\x60")


def split_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except Exception:
        return None, text
    return meta, parts[2]


def section_bodies(body: str) -> dict[str, str]:
    """Map each H2 heading to its raw body text (up to the next H2)."""
    result: dict[str, str] = {}
    parts = re.split(r"(?m)^## (.+?)\s*$", body)
    # parts = [pre, h1, body1, h2, body2, ...]
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip()
        result[heading] = parts[i + 1].strip()
    return result


def headings(body: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^## (.+?)\s*$", body, re.M)]


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)

    if not isinstance(meta, dict):
        errors.append("missing or invalid frontmatter")
        meta = {}
    name = str(meta.get("name") or "")
    desc = str(meta.get("description") or "")
    if not name:
        errors.append("frontmatter.name missing")
    if not desc:
        errors.append("frontmatter.description missing")
    if name and name != path.parent.name:
        errors.append("name %r != directory %r" % (name, path.parent.name))

    heads = headings(body)
    bodies = section_bodies(body)
    for required in REQUIRED:
        if required not in heads:
            errors.append("missing required section: " + required)
        elif not bodies.get(required):
            errors.append("empty required section: " + required)

    present_order = [h for h in heads if h in ORDER]
    expected_order = [h for h in ORDER if h in present_order]
    if present_order != expected_order:
        errors.append("canonical section order wrong: %s" % present_order)

    for ref in sorted(set(REF_PATTERN.findall(text))):
        candidate = ref.split("#")[0].rstrip("/")
        if "<" in candidate or "*" in candidate:
            continue
        if not (ROOT / candidate).exists():
            errors.append("referenced path missing: " + candidate)
    return errors


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    failed = 0
    for d in sorted(SKILLS.iterdir()):
        skill = d / "SKILL.md"
        if not skill.is_file():
            continue
        errors = check_file(skill)
        rel = skill.relative_to(ROOT)
        if errors:
            failed += 1
            print("FAIL " + str(rel))
            for e in errors:
                print("   - " + e)
        else:
            print("PASS " + str(rel))
    if failed:
        print()
        print("%d skill file(s) failed validation" % failed)
        return 1
    print()
    print("All skill files passed validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
