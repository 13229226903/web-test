---
task_id: 2026-11-09_stable_regression_3001
agent: orchestrator
status: completed
current_step: report_delivered
execution_mode: codex_single_context
task_type: stable_regression
human_gates_pending: []
target_url: http://10.17.1.66:3001/
artifact_registry: artifacts/regression_registry.md
base_url: http://10.17.1.66:3001/
include_status: stable_regression
excluded:
  - tests/test_infinite_canvas_enhance_v4.py
exclude_reason: Registry status is pending_fix, not stable_regression
runner: scripts/regression_runner.py (via run_regression_3001.py)
created_at: '2026-11-09 09:30:00'
---
# 调度历史
- [2026-11-09 09:30:00] route: stable_regression / registry stable tests / target 3001
- scope: 19 stable_regression suites; exclude enhance (pending_fix)


# 调度历史（续）
- [2026-11-09 09:35] user: 暂停跑，后端测试服挂了 → 已终止 runner，run aborted during 'portrait' suite，等待后端恢复

- [2026-11-09 09:40] user: 继续跑 → 后端已恢复，重新全量 19 套件，runner PID 27956

- [2026-11-09 14:20] ALL DONE 19/19 suites; total=308 clean=273 retry=9 failed=18 gate=failed; allure=reports/allure-report-regression-3001
