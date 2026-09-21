"""串行运行当前任务 run_manifest.json 中的归档回归脚本。

归档脚本从 registry Archive 列解析；每个 suite 独立进程、独立日志，
统一累积 Allure 原始结果到 reports/allure-results-archive。
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = (ROOT / "artifacts" / ".current_task").read_text(encoding="utf-8").strip()
TASK_DIR = ROOT / "artifacts" / TASK
BASE_URL = "http://10.17.1.66:3001"
RESULTS = ROOT / "reports" / "allure-results-archive"
LOG_DIR = TASK_DIR / "regression"
SUMMARY = LOG_DIR / "summary.json"

if RESULTS.parent != ROOT / "reports" or RESULTS.name != "allure-results-archive":
    raise SystemExit(f"拒绝清理非标准结果目录: {RESULTS}")
if RESULTS.exists():
    shutil.rmtree(RESULTS)
RESULTS.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

jobs = json.loads((TASK_DIR / "run_manifest.json").read_text(encoding="utf-8"))
rows = []
run_started = time.monotonic()

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

for idx, job in enumerate(jobs, 1):
    archive = job["archive"]
    safe_name = Path(archive).stem
    log_path = LOG_DIR / f"{safe_name}.log"
    cmd = [
        sys.executable, "-m", "pytest", archive, "-q",
        f"--base-url={BASE_URL}",
        "--alluredir=reports/allure-results-archive",
    ]
    print(f"\n=== START {idx}/{len(jobs)} {safe_name} :: {archive} ===", flush=True)
    append_progress(f"orchestrator step: run archive {archive}")
    started = time.monotonic()
    code = None
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3600,
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
        "feature": job["feature"],
        "task_id": job["task_id"],
        "archive": archive,
        "tests": job["tests"],
        "exit_code": code,
        "seconds": seconds,
        "counts": counts,
        "result": result,
        "log": f"artifacts/{TASK}/regression/{safe_name}.log",
    }
    rows.append(row)
    append_progress(
        f"orchestrator step: finished archive {archive} exit={code} "
        f"seconds={seconds} counts={counts} result={result}"
    )
    print(f"=== END {safe_name} exit={code} seconds={seconds} counts={counts} result={result} ===", flush=True)
    tail = "\n".join(text.splitlines()[-12:])
    if tail:
        print(tail, flush=True)
    SUMMARY.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

aggregate = {}
for row in rows:
    for key, value in row["counts"].items():
        aggregate[key] = aggregate.get(key, 0) + value
report = {
    "task_id": TASK,
    "base_url": BASE_URL,
    "archive_script_count": len(rows),
    "passed_suites": sum(1 for r in rows if r["result"] == "passed"),
    "suites_with_skips": sum(1 for r in rows if r["result"] == "passed_with_skips"),
    "failed_suites": sum(1 for r in rows if r["result"] in ("failed", "timeout")),
    "total_seconds": round(time.monotonic() - run_started, 2),
    "aggregate_counts": aggregate,
    "rows": rows,
}
SUMMARY.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
append_progress(
    f"orchestrator run_archived_regression finished: suites={len(rows)} "
    f"passed_suites={report['passed_suites']} skip_suites={report['suites_with_skips']} "
    f"failed_suites={report['failed_suites']} counts={aggregate} total_seconds={report['total_seconds']}"
)
print("\n=== FINAL SUMMARY ===")
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)