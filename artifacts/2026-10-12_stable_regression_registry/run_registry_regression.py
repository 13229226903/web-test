"""串行运行当前任务 run_manifest.json 中登记的 stable_regression 脚本（Tests 列）。

每个 suite 独立进程、独立日志；Allure 原始结果统一累积到
reports/allure-results-regression，供稳定回归报告使用。
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = Path(__file__).resolve().parent
TASK = TASK_DIR.name
BASE_URL = "http://10.17.1.66:3001"
RESULTS = ROOT / "reports" / "allure-results-regression"
LOG_DIR = TASK_DIR / "regression"
SUMMARY = LOG_DIR / "summary.json"

if RESULTS.parent != ROOT / "reports" or RESULTS.name != "allure-results-regression":
    raise SystemExit(f"拒绝清理非标准结果目录: {RESULTS}")
if RESULTS.exists():
    shutil.rmtree(RESULTS)
RESULTS.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

jobs = json.loads((TASK_DIR / "run_manifest.json").read_text(encoding="utf-8"))


def append_progress(text):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with (TASK_DIR / "progress.log").open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {text}\n")


def parse_counts(text):
    counts = {}
    for key in ("passed", "failed", "error", "errors", "skipped", "xfailed", "xpassed", "deselected"):
        vals = [int(x) for x in re.findall(r"(\d+)\s+" + key + r"\b", text)]
        if vals:
            counts[key] = max(vals)
    if "error" in counts and "errors" not in counts:
        counts["errors"] = counts.pop("error")
    return counts


rows = []
run_started = time.monotonic()
append_progress(f"orchestrator start: run {len(jobs)} registry stable_regression suites on {BASE_URL}")

for idx, job in enumerate(jobs, 1):
    script = job["tests"]
    safe_name = Path(script).stem
    log_path = LOG_DIR / f"{safe_name}.log"
    cmd = [
        sys.executable, "-m", "pytest", script, "-q",
        f"--base-url={BASE_URL}",
        "--alluredir=reports/allure-results-regression",
    ]
    print(f"\n=== START {idx}/{len(jobs)} {safe_name} :: {script} ===", flush=True)
    append_progress(f"orchestrator step: run suite {script}")
    started = time.monotonic()
    code = None
    try:
        proc = subprocess.run(
            cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=5400,
        )
        text = proc.stdout or ""
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        text = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        code = "timeout"
    seconds = round(time.monotonic() - started, 2)
    log_path.write_text(text, encoding="utf-8")
    counts = parse_counts(text)
    failed = counts.get("failed", 0) + counts.get("errors", 0)
    if code == "timeout":
        result = "timeout"
    elif code != 0 or failed:
        result = "failed"
    elif counts.get("skipped", 0) or counts.get("xfailed", 0) or counts.get("xpassed", 0):
        result = "passed_with_skips"
    else:
        result = "passed"
    row = {
        "feature": job["feature"], "task_id": job["task_id"], "tests": script,
        "archive": job["archive"], "exit_code": code, "seconds": seconds,
        "counts": counts, "result": result,
        "log": f"artifacts/{TASK}/regression/{safe_name}.log",
    }
    rows.append(row)
    append_progress(
        f"orchestrator step: finished suite {script} exit={code} seconds={seconds} "
        f"counts={counts} result={result}"
    )
    print(f"=== END {safe_name} exit={code} seconds={seconds} counts={counts} result={result} ===", flush=True)
    tail = "\n".join([l for l in text.splitlines() if re.search(r"(PASSED|FAILED|ERROR|Skipped|passed|failed|error)", l)][-15:]) or "\n".join(text.splitlines()[-12:])
    print(tail, flush=True)
    SUMMARY.write_text(json.dumps({"rows": rows, "complete": False}, ensure_ascii=False, indent=2), encoding="utf-8")

aggregate = {}
for row in rows:
    for key, value in row["counts"].items():
        aggregate[key] = aggregate.get(key, 0) + value
report = {
    "task_id": TASK, "base_url": BASE_URL, "suite_count": len(rows),
    "passed_suites": sum(1 for r in rows if r["result"] == "passed"),
    "suites_with_skips": sum(1 for r in rows if r["result"] == "passed_with_skips"),
    "failed_suites": sum(1 for r in rows if r["result"] in ("failed", "timeout")),
    "total_seconds": round(time.monotonic() - run_started, 2),
    "aggregate_counts": aggregate, "complete": True, "rows": rows,
}
SUMMARY.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
append_progress(
    f"orchestrator run finished: suites={len(rows)} passed_suites={report['passed_suites']} "
    f"skip_suites={report['suites_with_skips']} failed_suites={report['failed_suites']} "
    f"counts={aggregate} total_seconds={report['total_seconds']}"
)
print("\n=== FINAL SUMMARY ===")
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
