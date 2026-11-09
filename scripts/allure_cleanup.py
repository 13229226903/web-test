#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Allure 报告清理工具：每次生成新报告前，清掉 reports/ 下的旧报告。

背景
----
`pytest.ini` 的 `--alluredir=reports/allure-results` 若不清空，多轮运行会把
同一 case 的结果混在同一目录，Allure 报告出现重复用例、截图新旧混杂
（2026-11-04 实测：同一 case 出现 2 条记录）。

用法
----
    # 查看将删除哪些目录（不实际删除）
    python scripts/allure_cleanup.py --dry-run

    # 清理 reports/ 下所有旧的 allure-*，只保留本次要用的目录
    python scripts/allure_cleanup.py --keep allure-results-matrix --keep allure-report-matrix

    # 若需保护归档文档引用的目录
    python scripts/allure_cleanup.py --protect-archived --keep allure-results-matrix

    # 只清理报告目录（保留结果目录，便于重新 generate）
    python scripts/allure_cleanup.py --reports-only

规则
----
- 只作用于 `reports/` 下，目录名以 `allure-` 开头；
- **不清理 `reports/attempts/`**（跨轮 flaky 分析数据源，必须保留）；
- 不触碰 `artifacts/`、`archive/`、`page_map/` 等其它目录；
- `--dry-run` 只打印删除清单；
- 默认删除 reports/ 下所有 `allure-*` 目录（只保留 `--keep` 指定的）；
- 加 `--protect-archived` 可保护被归档文档引用的目录（`artifacts/**/*.md` 中出现
  `reports/<dir>`），用于需要保留历史证据的场景。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ARTIFACTS = ROOT / "artifacts"

REPORT_PREFIX = "allure-"
# 明确保护：attempts/ 不以 allure- 开头，因此 targets() 永远不会选中它。
PROTECTED_DIRS = ("attempts", "flaky")


def referenced_dirs() -> set[str]:
    """扫描 artifacts/**/*.md，收集被引用到的 reports/<dir>。"""
    refs: set[str] = set()
    if not ARTIFACTS.exists():
        return refs
    pattern = re.compile(r"reports/(allure-[A-Za-z0-9_.\-]+)")
    for md in ARTIFACTS.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for name in pattern.findall(text):
            refs.add(name.rstrip("/"))
    return refs


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def targets(reports_only: bool) -> list[Path]:
    if not REPORTS.exists():
        return []
    out: list[Path] = []
    for p in sorted(REPORTS.iterdir()):
        if not p.is_dir() or not p.name.startswith(REPORT_PREFIX):
            continue
        if p.name in PROTECTED_DIRS:
            continue
        if reports_only and p.name.startswith("allure-results"):
            continue
        out.append(p)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="清理旧 Allure 报告目录")
    parser.add_argument("--keep", action="append", default=[],
                        help="要保留的目录名（可重复），如 allure-results-matrix")
    parser.add_argument("--reports-only", action="store_true",
                        help="只清理 allure-report-*，保留 allure-results-*")
    parser.add_argument("--protect-archived", action="store_true",
                        help="保护被 artifacts/**/*.md 引用的归档报告目录（默认不保护，全部清理）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不删除")
    args = parser.parse_args()

    keep = set(args.keep)
    refs = referenced_dirs()
    planned: list[Path] = []
    skipped_ref: list[Path] = []
    skipped_keep: list[Path] = []

    for p in targets(args.reports_only):
        if p.name in keep:
            skipped_keep.append(p)
            continue
        if args.protect_archived and p.name in refs:
            skipped_ref.append(p)
            continue
        planned.append(p)

    total_mb = sum(dir_size(p) for p in planned) / 1024 / 1024
    print(f"[allure-cleanup] root={ROOT}")
    print(f"[allure-cleanup] 待删除 {len(planned)} 个目录，共 {total_mb:.1f} MB")
    for p in planned:
        print(f"  DELETE  {p.name:45s} {dir_size(p)/1024/1024:8.1f} MB")
    if skipped_keep:
        print(f"[allure-cleanup] 保留（--keep）：{', '.join(p.name for p in skipped_keep)}")
    if skipped_ref:
        print(f"[allure-cleanup] 保留（--protect-archived 命中归档引用）：{', '.join(p.name for p in skipped_ref)}")
    if args.dry_run:
        print("[allure-cleanup] dry-run：未实际删除")
        return 0

    for p in planned:
        shutil.rmtree(p, ignore_errors=True)
    print(f"[allure-cleanup] 已删除 {len(planned)} 个目录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
