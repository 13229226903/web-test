#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared stable-regression runner (serial by design).

Responsibilities
----------------
- run registry suites one by one, with a single retry by default;
- keep a stable run_id across every suite in this invocation;
- persist suite-level results for auditable stop/continue;
- invoke scripts/regression_summary.py at the end to produce the honest
  clean/retry/quarantine summary.

Parallel execution is intentionally NOT implemented here. Enable it only after
account/data isolation metadata is available for every suite.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 复用 regression_summary 的判定逻辑做「逐套件」结论，避免两处口径漂移。
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from regression_summary import _classify, _load_attempts, _load_quarantine  # noqa: E402
except Exception:  # pragma: no cover - summary 必须存在；缺失时降级为不判定
    _classify = None
    _load_attempts = None
    _load_quarantine = None

# (显示名, 路径, 英文别名) —— 别名字段供 --suites 按需选择时输入（中文名不便输入）。
SUITES = [
    ("人像检测三入口页", "tests/test_pokecut_portrait_detector.py", "portrait"),
    ("AI Image Text Enhancer", "tests/test_ai_image_text_enhancer_experiment.py", "ai-text"),
    ("画布页文字功能", "tests/test_infinite_canvas_text_layer_v2.py", "canvas-text"),
    ("Mobile Home v3", "tests/test_mobile_home.py", "mobile-home"),
    ("帮助中心", "tests/test_help_page.py", "help"),
    ("检测类功能适配 UI", "tests/test_detection_ui_seo_l6.py", "detection"),
    ("PC 首页 Home v6", "tests/test_pokecut_pc_home_v6.py", "pc-home"),
    ("PC 批量编辑 Batch v1", "tests/test_pokecut_pc_batch_v1.py", "pc-batch"),
    ("旧画布 Insert 面板", "tests/test_old_canvas_insert_panel_v3.py", "insert-panel"),
    ("旧画布文字 Text 面板", "tests/test_old_canvas_text_panel_v1.py", "old-text-panel"),
    ("旧画布贴纸调参面板", "tests/test_old_canvas_sticker_panel_v1.py", "old-sticker-panel"),
    ("SEO 主上传交互（PC）", "tests/test_seo_main_upload_interactions_v1.py", "seo-pc"),
    ("SEO 主上传交互（移动端）", "tests/mobile/test_seo_main_upload_mobile_v1.py", "seo-mobile"),
    ("Create/Chat Auto 意图识别", "tests/test_create_chat_to_edit_auto_v1.py", "create-auto"),
    ("画布统计优化 40 条", "tests/test_canvas_stats_all.py", "canvas-stats"),
    ("旧画布 AI Tools", "tests/test_old_canvas_ai_tools_all.py", "ai-tools"),
    ("无限画布贴纸调整", "tests/test_infinite_canvas_sticker_v1.py", "sticker"),
    ("Batch Edit 面板（/agent）", "tests/test_agent_batch_edit_panel.py", "agent-batch"),
    ("Create 模型矩阵", "tests/test_create_chat_to_edit_model_matrix_v1.py", "model-matrix"),
    ("无限画布 Enhance 2K/4K/8K", "tests/test_infinite_canvas_enhance_v4.py", "enhance"),
]


def _select_suites(spec: str | None, log_fn=None) -> list[tuple[str, str, str]]:
    """按 --suites 选择套件；None/空 => 全量。

    每个 token 依次尝试匹配：英文别名（精确，大小写不敏感）> 路径片段 > 显示名子串。
    未匹配的 token 会明确报错，避免「静默少跑」。
    """
    if not spec:
        return list(SUITES)
    tokens = [t.strip() for t in spec.split(",") if t.strip()]
    chosen: list[tuple[str, str, str]] = []
    unmatched: list[str] = []
    for tok in tokens:
        low = tok.lower()
        hit = None
        for item in SUITES:
            if item[2].lower() == low:
                hit = item
                break
        if hit is None:
            for item in SUITES:
                if low in item[1].lower() or tok in item[0]:
                    hit = item
                    break
        if hit is None:
            unmatched.append(tok)
        elif hit not in chosen:
            chosen.append(hit)
    if unmatched:
        avail = ", ".join(f"{it[2]}" for it in SUITES)
        raise SystemExit(f"unknown suite token(s): {', '.join(unmatched)}\navailable aliases: {avail}")
    return chosen


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serial stable-regression runner with attempt-level reporting")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--label", required=True, help="short report label, e.g. 3001")
    parser.add_argument("--reruns", type=int, default=1, help="pytest-rerunfailures rerun count; default 1")
    parser.add_argument("--no-reruns", action="store_true", help="disable retries for this run")
    parser.add_argument("--resume", action="store_true", help="skip suites already present in suite_results.json")
    parser.add_argument("--summary-gate-mode", choices=("strict", "allow-retry", "report-only"), default="allow-retry")
    parser.add_argument("--fail-on-xfail", action="store_true", help="make xfail block the summary gate")
    parser.add_argument("--fail-on-skipped", action="store_true", help="make skipped block the summary gate")
    parser.add_argument("--suites", default=None,
                        help="按需只跑指定套件，逗号分隔；支持英文别名/路径片段/显示名。不带则跑全量。"
                             "例：--suites pc-home,mobile-home")
    parser.add_argument("--list-suites", action="store_true",
                        help="列出全部套件（别名 / 显示名 / 路径）后退出")
    parser.add_argument("--fail-fast", action="store_true",
                        help="stop at the first suite whose verdict is not clean (default: keep going)")
    parser.add_argument("--auto-flaky-retry", dest="auto_flaky_retry", action="store_true", default=True,
                        help="after a suite, re-run its failing cases once to separate flaky from real failures (default: on)")
    parser.add_argument("--no-auto-flaky-retry", dest="auto_flaky_retry", action="store_false",
                        help="disable the automatic flaky re-check")
    parser.add_argument("--dry-run", action="store_true", help="print planned paths without running suites")
    return parser.parse_args(argv)


def _run_id() -> str:
    return os.environ.get("REGRESSION_RUN_ID") or f"reg-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _failing_nodeids(attempt_log: Path, run_id: str, suite_path: str) -> list[str]:
    """从 attempt 记录里取出该套件本次失败的 test_id（用于定向复跑）。"""
    if _load_attempts is None:
        return []
    try:
        records = [r for r in _load_attempts(attempt_log)
                   if str(r.get("run_id")) == run_id
                   and str(r.get("test_id") or "").startswith(suite_path)]
    except Exception:
        return []
    grouped: dict[str, list[dict]] = {}
    for r in records:
        grouped.setdefault(str(r.get("test_id") or ""), []).append(r)
    bad = []
    for test_id, group in grouped.items():
        group.sort(key=lambda r: ({"setup": 0, "call": 1, "teardown": 2}.get(str(r.get("phase")), 9),
                                  int(r.get("attempt") or 0)))
        call = [r for r in group if r.get("phase") == "call"]
        final = call[-1] if call else None
        st_failed = any(r.get("phase") in {"setup", "teardown"} and str(r.get("outcome")) == "failed"
                        for r in group)
        if st_failed or (final is not None and str(final.get("outcome")) == "failed"):
            bad.append(test_id)
    return bad


def _rerun_flaky(relative_path: str, nodeids: list[str], base_url: str, env: dict,
                 allure_dir: Path, log_fn, recheck_run_id: str, recheck_log: Path) -> dict:
    """定向复跑失败用例一次；返回 {all_passed, tail}。

    关键：复跑使用**独立 run_id 与独立 attempt log**，否则复跑记录会混进主 run 的
    attempt 记录，使整体 summary 把「已判为 flaky 的用例」仍计成 failed（口径污染）。
    """
    if not nodeids:
        return {}
    cmd = [sys.executable, "-m", "pytest", *nodeids, "-q",
           f"--base-url={base_url}", f"--alluredir={allure_dir}"]
    child_env = dict(env)
    child_env["REGRESSION_RUN_ID"] = recheck_run_id
    child_env["PYTEST_ATTEMPT_LOG"] = str(recheck_log)
    log_fn(f"  FLAKY-RECHECK: re-running {len(nodeids)} failing case(s) once ...")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=child_env)
    tail = "\n".join(line for line in ((proc.stdout or "") + "\n" + (proc.stderr or "")).splitlines() if line.strip())[-600:]
    log_fn(f"  FLAKY-RECHECK done rc={proc.returncode}")
    return {"all_passed": proc.returncode == 0, "tail": tail}


def _suite_verdict(attempt_log: Path, run_id: str, suite_path: str, quarantine_path: Path) -> dict:
    """对单个套件（一个测试文件）给出结论：各状态计数 + 是否含阻塞态。

    阻塞态 = 与整体门禁同口径（strict: retry/failed/broken；allow-retry: failed/broken）。
    复用 regression_summary._classify，保证「逐套件」与「整体」判定一致。
    """
    if _classify is None or _load_attempts is None:
        return {"available": False, "blocking": [], "counts": {}}
    try:
        records = [r for r in _load_attempts(attempt_log)
                   if str(r.get("run_id")) == run_id
                   and str(r.get("test_id") or "").startswith(suite_path)]
    except Exception:
        return {"available": False, "blocking": [], "counts": {}}
    quar, _errs = _load_quarantine(quarantine_path)
    grouped: dict[str, list[dict]] = {}
    for r in records:
        grouped.setdefault(str(r.get("test_id") or ""), []).append(r)
    today = dt.date.today()
    counts: dict[str, int] = {}
    blocking: list[str] = []
    for test_id, group in grouped.items():
        group.sort(key=lambda r: ({"setup": 0, "call": 1, "teardown": 2}.get(str(r.get("phase")), 9),
                                  int(r.get("attempt") or 0)))
        raw_cid = str(group[-1].get("case_id") or "")
        # 可读标识：优先 case_id（若已解析），否则用 allure 标题，最后退化为 nodeid 尾段
        if raw_cid and not raw_cid.startswith("MISSING_CASE_ID:"):
            cid = raw_cid
        else:
            cid = str(group[-1].get("title") or test_id.split("::")[-1])
        # 隔离登记用的是解析后的 case_id；MISSING 时按 nodeid 兜底查询
        status, reason = _classify(group, quar.get(raw_cid) or quar.get(cid), today)
        counts[status] = counts.get(status, 0) + 1
        if status in ("failed", "broken"):
            blocking.append(f"{cid} [{status}] {reason[:120]}")
    return {"available": True, "blocking": blocking, "counts": counts}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # --list-suites：只列清单后退出（方便确认别名）
    if getattr(args, "list_suites", False):
        print("可用套件（--suites 用别名）：")
        for name, path, alias in SUITES:
            print(f"  {alias:<20} {name:<28} {path}")
        return 0

    # --suites：按需只跑指定套件（不带则全量）
    selected_suites = _select_suites(getattr(args, "suites", None))

    if args.no_reruns:
        args.reruns = 0
    if args.reruns > 0 and importlib.util.find_spec("pytest_rerunfailures") is None:
        print("pytest-rerunfailures is required for --reruns > 0. Install it or pass --no-reruns.", file=sys.stderr)
        return 2

    run_id = _run_id()
    base_url = args.base_url.rstrip("/")
    label = args.label
    out_dir = ROOT / "reports" / f"regression-{label}" / run_id
    allure_dir = ROOT / "reports" / f"allure-results-regression-{label}"
    attempt_log = ROOT / "reports" / "attempts" / f"{run_id}.jsonl"
    result_path = out_dir / "suite_results.json"
    log_path = out_dir / "run.log"

    env = dict(os.environ)
    env["POKECUT_BASE_URL"] = base_url
    env["REGRESSION_RUN_ID"] = run_id
    env["PYTEST_ATTEMPT_LOG"] = str(attempt_log)

    def log(message: str) -> None:
        line = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        print(line, flush=True)
        if args.dry_run:
            return
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    log(f"START run_id={run_id} base_url={base_url} reruns={args.reruns} resume={args.resume} "
        f"suites={'ALL' if not getattr(args, 'suites', None) else len(selected_suites)}")
    if args.dry_run:
        log(f"DRY-RUN out_dir={out_dir} allure_dir={allure_dir} attempt_log={attempt_log}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    attempt_log.parent.mkdir(parents=True, exist_ok=True)
    if attempt_log.exists():
        attempt_log.unlink()
    if not args.resume and allure_dir.exists():
        shutil.rmtree(allure_dir, ignore_errors=True)
    allure_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    done: set[str] = set()
    if args.resume and result_path.exists():
        try:
            results = json.loads(result_path.read_text(encoding="utf-8"))
            done = {str(item.get("suite")) for item in results if isinstance(item, dict)}
        except Exception:
            results = []
            done = set()

    started = time.time()
    for name, relative_path, _alias in selected_suites:
        if name in done:
            log(f"SKIP already-recorded suite: {name}")
            continue
        log(f"RUN START: {name} {relative_path}")
        command = [
            sys.executable, "-m", "pytest", relative_path, "-q",
            f"--base-url={base_url}",
            f"--alluredir={allure_dir}",
        ]
        if args.reruns > 0:
            command.extend(["--reruns", str(args.reruns)])
        suite_started = time.time()
        proc = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env,
        )
        duration = round(time.time() - suite_started, 1)
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        suite_log = out_dir / f"suite_{name.replace('/', '_').replace(' ', '_')}.log"
        suite_log.write_text(output, encoding="utf-8")
        tail = "\n".join(line for line in output.splitlines() if line.strip())[-2000:]
        record = {
            "suite": name,
            "path": relative_path,
            "returncode": proc.returncode,
            "duration_s": duration,
            "log": str(suite_log.relative_to(ROOT)).replace("\\", "/"),
            "tail": tail,
        }
        # —— 自动 flaky 分类（2026-11-08）——
        # 套件若有失败，定向复跑失败用例一次：全通过 => 判为 flaky（环境/时序），
        # 仍失败 => 真失败。这一步替代「人工事后复跑归因」，手动跑一次就能分清。
        flaky_note = ""
        if args.auto_flaky_retry and proc.returncode != 0:
            bad = _failing_nodeids(attempt_log, run_id, relative_path)
            if bad:
                rerun_dir = allure_dir.parent / f"allure-flaky-recheck-{run_id}-{abs(hash(relative_path)) % 10000}"
                rerun_dir.mkdir(parents=True, exist_ok=True)
                recheck_run_id = f"{run_id}:flaky-recheck:{abs(hash(relative_path)) % 10000}"
                recheck_log = out_dir / f"flaky_recheck_{name.replace('/', '_').replace(' ', '_')}.jsonl"
                rr = _rerun_flaky(relative_path, bad, base_url, env, rerun_dir, log,
                                  recheck_run_id, recheck_log)
                record["flaky_recheck"] = {"failing": len(bad), "all_passed": rr.get("all_passed")}
                if rr.get("all_passed"):
                    flaky_note = f"（{len(bad)} 条失败复跑全通过 → 全部判为 FLAKY，非稳定失败）"
                else:
                    flaky_note = f"（{len(bad)} 条失败复跑仍有失败 → 存在稳定失败）"

        # —— 逐套件结论（2026-11-08）——
        # 手动跑回归时最痛的是「要等全部套件跑完才知道结论」。这里每套件跑完立即判定并打印，
        # 而不是等到最后；判定口径复用 regression_summary._classify（与整体门禁一致）。
        verdict = _suite_verdict(attempt_log, run_id, relative_path,
                                 ROOT / "artifacts" / "regression_quarantine.yaml")
        record["verdict"] = verdict
        results.append(record)
        _write_json(result_path, results)
        log(f"RUN DONE: {name} rc={proc.returncode} {duration}s{flaky_note}")
        if verdict.get("available"):
            c = verdict["counts"]
            summary_line = " ".join(f"{k}={v}" for k, v in sorted(c.items()))
            status = "BLOCKING" if verdict["blocking"] else "ok"
            log(f"  VERDICT [{status}] {name}: {summary_line or 'no cases recorded'}")
            for item in verdict["blocking"][:5]:
                log(f"    - {item}")
        else:
            log(f"  VERDICT [unknown] {name}: attempt-level verdict unavailable")

        # fail-fast：触线即停，避免白等剩余套件（手动跑时尤其重要）。
        # 注意：自动 flaky 复跑已先行完成，故这里停下的都是「复跑仍失败」或「未被复跑覆盖」的阻塞态。
        if args.fail_fast and verdict.get("blocking"):
            log(f"FAIL-FAST: stopping after '{name}'（该套件存在阻塞态；剩余套件未运行）")
            break

    summary_cmd = [
        sys.executable, str(ROOT / "scripts" / "regression_summary.py"),
        "--attempt-log", str(attempt_log),
        "--allure-dir", str(allure_dir),
        "--out-dir", str(out_dir),
        "--gate-mode", args.summary_gate_mode,
    ]
    if args.fail_on_xfail:
        summary_cmd.append("--fail-on-xfail")
    if args.fail_on_skipped:
        summary_cmd.append("--fail-on-skipped")
    summary_proc = subprocess.run(summary_cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (out_dir / "summary.log").write_text((summary_proc.stdout or "") + "\n" + (summary_proc.stderr or ""), encoding="utf-8")
    log(f"SUMMARY rc={summary_proc.returncode} {summary_proc.stdout.strip()}")
    log(f"ALL DONE in {round(time.time() - started, 1)}s")

    suite_failures = [item for item in results if int(item.get("returncode") or 0) != 0]
    ran = {str(item.get("suite")) for item in results}
    not_run = [name for name, _p, _a in (SUITES if not getattr(args, "suites", None) else selected_suites)
               if name not in ran]
    if not_run:
        log(f"NOT RUN ({len(not_run)} suites): {', '.join(not_run)}")
    return 1 if suite_failures or summary_proc.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
