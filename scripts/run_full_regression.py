#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整回归测试（SEO regression + 独立脚本 + attempt 汇总门禁 + Allure）。

用法：
    python scripts/run_full_regression.py [--headed] [--base-url URL]

流程：
    1. 生成 run_id，准备 attempt 日志与 allure 结果目录
    2. pytest -m regression（SEO/功能回归）
    3. 独立脚本验证（verify_help_vue.py 等）
    4. 只删除被独立脚本明确替代的重复结果，保留 xfail/skip/broken
    5. 生成 regression_summary.json / .md（门禁数据源）
    6. 生成 Allure 报告
    7. 退出码 = suite 结果 OR 汇总门禁结果

门禁语义（2026-11-05）：
    - 退出码反映 regression_summary 的 gate.status，而不只是 pytest 是否红。
    - 发布 / 归档证据必须同时给出 clean_pass_rate / retry_pass / quarantined。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="完整回归测试（含汇总门禁）")
    parser.add_argument("--headed", action="store_true", help="浏览器可见模式")
    parser.add_argument("--base-url", default="http://10.17.1.66:3102",
                        help="测试环境 URL，默认 http://10.17.1.66:3102")
    parser.add_argument("--no-report", action="store_true", help="不生成 Allure 报告")
    parser.add_argument("--no-standalone", action="store_true", help="跳过独立脚本验证")
    parser.add_argument("--label", default="full", help="报告标签，用于输出目录命名")
    parser.add_argument("--pytest-target", default="tests/",
                        help="pytest 目标路径（默认 tests/；调试时可指定单文件）")
    parser.add_argument("--marker", default="regression",
                        help="pytest -m 标记（默认 regression；传空字符串则不过滤）")
    parser.add_argument("--summary-gate-mode", choices=("strict", "allow-retry", "report-only"),
                        default="allow-retry", help="汇总门禁模式")
    parser.add_argument("--reruns", type=int, default=0,
                        help="pytest-rerunfailures 重试次数；默认 0（该路径默认不重试）")
    parser.add_argument("--fail-on-xfail", action="store_true", help="xfail 计入门禁失败")
    parser.add_argument("--fail-on-skipped", action="store_true", help="skipped 计入门禁失败")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    python = sys.executable or "python"

    run_id = os.environ.get("REGRESSION_RUN_ID") or f"full-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    out_dir = ROOT / "reports" / f"regression-{args.label}" / run_id
    allure_dir = ROOT / "reports" / "allure-results"
    allure_report = ROOT / "reports" / "allure-report"
    attempt_log = ROOT / "reports" / "attempts" / f"{run_id}.jsonl"

    out_dir.mkdir(parents=True, exist_ok=True)
    attempt_log.parent.mkdir(parents=True, exist_ok=True)
    if attempt_log.exists():
        attempt_log.unlink()

    # 1. 清理旧报告，保留本轮目录
    os.makedirs(allure_dir, exist_ok=True)
    subprocess.run(
        [python, str(ROOT / "scripts" / "allure_cleanup.py"),
         "--keep", "allure-results", "--keep", "allure-report"],
        cwd=ROOT,
    )
    for name in os.listdir(allure_dir):
        path = os.path.join(allure_dir, name)
        shutil.rmtree(path, ignore_errors=True) if os.path.isdir(path) else os.remove(path)

    env = dict(os.environ)
    env["POKECUT_BASE_URL"] = args.base_url
    env["REGRESSION_RUN_ID"] = run_id
    env["PYTEST_ATTEMPT_LOG"] = str(attempt_log)

    suite_results: list[dict[str, object]] = []

    # 2. pytest 回归
    print("\n=== 1/5 pytest 回归 ===\n")
    pytest_args = [
        python, "-m", "pytest", args.pytest_target, "-v",
        f"--base-url={args.base_url}",
        f"--alluredir={allure_dir}",
    ]
    if args.marker:
        pytest_args.extend(["-m", args.marker])
    if args.headed:
        pytest_args.append("--headed")
    if args.reruns > 0:
        pytest_args.extend(["--reruns", str(args.reruns)])
    r1 = subprocess.run(pytest_args, cwd=ROOT, env=env)
    suite_results.append({"suite": "pytest -m regression", "returncode": r1.returncode})

    # 3. 独立脚本验证
    if not args.no_standalone:
        for rel in ("scripts/verify_help_vue.py", "scripts/verify_homepage_vue.py"):
            spath = ROOT / rel
            if spath.exists():
                print(f"\n=== 2/5 独立脚本 {rel} ===\n")
                rc = subprocess.run([python, str(spath)], cwd=ROOT, env=env).returncode
                suite_results.append({"suite": rel, "returncode": rc})

    # 4. 只删除「被独立脚本明确替代」的重复结果；xfail/skip/broken 一律保留
    print("\n=== 3/5 清理已替代的重复结果 ===\n")
    subprocess.run([python, str(ROOT / "scripts" / "cleanup_xfailed.py")], cwd=ROOT)

    # 5. 生成汇总门禁。注意：独立脚本不写 attempt 日志，因此若 pytest 一条都没跑到，
    #    汇总会缺数据；此时显式报错而不是伪装通过。
    print("\n=== 4/5 生成汇总门禁 ===\n")
    summary_cmd = [
        python, str(ROOT / "scripts" / "regression_summary.py"),
        "--attempt-log", str(attempt_log),
        "--allure-dir", str(allure_dir),
        "--out-dir", str(out_dir),
        "--gate-mode", args.summary_gate_mode,
    ]
    if args.fail_on_xfail:
        summary_cmd.append("--fail-on-xfail")
    if args.fail_on_skipped:
        summary_cmd.append("--fail-on-skipped")

    if not attempt_log.exists() or attempt_log.stat().st_size == 0:
        message = (
            f"attempt log missing/empty: {attempt_log}\n"
            "no pytest attempts were recorded, so the gate cannot be evaluated."
        )
        (out_dir / "summary.log").write_text(message, encoding="utf-8")
        print(message, file=sys.stderr)
        return 2

    summary_proc = subprocess.run(summary_cmd, cwd=ROOT, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
    (out_dir / "summary.log").write_text(
        (summary_proc.stdout or "") + "\n" + (summary_proc.stderr or ""), encoding="utf-8"
    )
    print(summary_proc.stdout, end="")
    if summary_proc.stderr:
        print(summary_proc.stderr, end="", file=sys.stderr)

    # 6. 生成 Allure 报告
    if not args.no_report:
        print("\n=== 5/5 生成 Allure 报告 ===\n")
        subprocess.run(["allure", "generate", allure_dir, "-o", allure_report, "--clean"], cwd=ROOT)
        print(f"报告已生成: {allure_report}/index.html")

    suite_failures = [item for item in suite_results if int(item.get("returncode") or 0) != 0]
    summary_json = out_dir / "regression_summary.json"
    gate_failed = summary_proc.returncode != 0

    if summary_json.exists():
        try:
            data = json.loads(summary_json.read_text(encoding="utf-8"))
            counts = data.get("counts", {})
            rates = data.get("rates", {})
            print(
                "\n[gate] "
                f"status={data.get('gate', {}).get('status')} "
                f"clean_pass={counts.get('clean_pass')} "
                f"retry_pass={counts.get('retry_pass')} "
                f"quarantined={counts.get('quarantined')} "
                f"clean_pass_rate={rates.get('clean_pass_rate')}"
            )
        except Exception:
            pass

    if suite_failures or gate_failed:
        print("\n=== 回归结果：FAIL（suite 失败或门禁未通过） ===")
        return 1
    print("\n=== 回归结果：PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
