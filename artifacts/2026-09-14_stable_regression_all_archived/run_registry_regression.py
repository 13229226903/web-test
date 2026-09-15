"""串行复跑 regression_registry.md 中全部已归档回归脚本。

用法: python artifacts/<task_id>/run_registry_regression.py
结果: artifacts/<task_id>/regression/<name>.log + summary.json + reports/allure-results-regression
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
RESULTS = ROOT / "reports" / "allure-results-regression"

# 清理上一次的 allure 结果目录
RESULTS.mkdir(parents=True, exist_ok=True)
for path in RESULTS.iterdir():
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()

# 从 registry 解析 Tests / Archive 两列，执行 Archive 列脚本
registry = (ROOT / "artifacts" / "regression_registry.md").read_text(encoding="utf-8")
jobs = []
for line in registry.splitlines():
    if not line.startswith("|"):
        continue
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cols) < 13 or cols[0] in ("Feature",) or re.fullmatch(r"[-: ]+", cols[0]):
        continue
    tests, archive, status = cols[4], cols[5], cols[2]
    target = ROOT / tests
    if not target.is_file():
        jobs.append({"script": tests, "missing": True, "status": status, "archive": archive})
        continue
    jobs.append({"script": tests, "path": str(target), "status": status, "archive": archive,
                 "name": Path(tests).stem})

rows = []
for job in jobs:
    name = job.get("name") or Path(job["script"]).stem
    if job.get("missing"):
        rows.append({"name": name, "script": job["script"], "exit_code": None, "result": "missing_script"})
        continue
    log_path = TASK_DIR / "regression" / f"{name}.log"
    started = time.monotonic()
    print(f"\n=== START {name} :: {job['script']} ===", flush=True)
    with (TASK_DIR / "progress.log").open("a", encoding="utf-8") as p:
        p.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] orchestrator step: run {job['script']}\n")
    cmd = [sys.executable, "-m", "pytest", job["script"], "-q",
           f"--base-url={BASE_URL}", "--alluredir=reports/allure-results-regression"]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        try:
            proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                  text=True, encoding="utf-8", errors="replace", timeout=2700)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    seconds = round(time.monotonic() - started, 2)
    text = log_path.read_text(encoding="utf-8", errors="replace")
    counts = {}
    for key in ("passed", "failed", "error", "errors", "skipped", "xfailed", "xpassed", "deselected"):
        m = re.findall(r"(\d+) " + key + r"\b", text)
        if m:
            counts[key] = int(m[-1])
    row = {"name": name, "script": job["script"], "archive": job.get("archive"), "status": job["status"], "exit_code": code,
           "seconds": seconds, "counts": counts, "log": f"artifacts/{TASK}/regression/{name}.log"}
    rows.append(row)
    with (TASK_DIR / "progress.log").open("a", encoding="utf-8") as p:
        p.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] orchestrator step: finished {job['script']} exit={code} seconds={seconds} counts={counts}\n")
    print(f"=== END {name} exit={code} seconds={seconds} counts={counts} ===", flush=True)
    print("\n".join(text.splitlines()[-6:]), flush=True)

(TASK_DIR / "regression" / "summary.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n=== SUMMARY ===")
print(json.dumps(rows, ensure_ascii=False, indent=2))