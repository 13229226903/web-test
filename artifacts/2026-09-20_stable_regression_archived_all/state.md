---
task_id: 2026-09-20_stable_regression_archived_all
agent: orchestrator
status: completed
current_step: final_report
execution_mode: codex_single_context
task_type: stable_regression
human_gates_pending: []
agent_call_count:
  page-map-sync: 0
  test-case-design: 0
  test-writing: 0
  review: 0
  visual-review: 0
created_at: 2026-09-20 18:07:21
requirement_doc: artifacts/regression_registry.md
target_url: http://10.17.1.66:3001/
entry_url: http://10.17.1.66:3001/
entry_path: /
scope: 复跑 regression_registry.md 中 URL 登记为 http://10.17.1.66:3001 的 stable_regression 条目 archive/ 归档副本
stop_at: final_report
exploration_driver: none
diagnostic_driver: none
forbidden: 全量探索、修改断言、弱化预期、上传 test_images/ 以外素材
assets: 账号按各任务 confirmed artifact 与 PROJECT.md；素材 test_images/；环境 http://10.17.1.66:3001/
assumptions:
  - 用户明确要求执行已归档脚本，因此以 Archive 列为执行目标，而非 Tests 列当前脚本。
  - 仅纳入 URL 列登记为 10.17.1.66:3001 的 stable_regression 条目；dev 域条目与 pending_fix 条目排除。
  - 串行执行，单个脚本失败不阻断后续；仅报告结果，不自动修脚本。
artifacts:
  logs: artifacts/2026-09-20_stable_regression_archived_all/regression/
  summary: artifacts/2026-09-20_stable_regression_archived_all/regression/summary.json
  report: artifacts/2026-09-20_stable_regression_archived_all/report.md
  allure_results: reports/allure-results-archive
  allure_report: reports/allure-report-archive
next_step: completed
blockers: []
---
# 调度历史
- 2026-09-20 18:07:21 orchestrator route: stable_regression / run archived scripts matching target URL from registry