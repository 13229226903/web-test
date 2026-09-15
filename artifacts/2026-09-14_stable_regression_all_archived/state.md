---
task_id: 2026-09-14_stable_regression_all_archived
agent: orchestrator
status: archived
current_step: archived
execution_mode: codex_single_context
task_type: stable_regression
human_gates_pending: []
agent_call_count:
  page-map-sync: 0
  test-case-design: 0
  test-writing: 0
  review: 0
  visual-review: 0
created_at: 2026-09-14 15:41:07
target_url: http://10.17.1.66:3001/
entry_url: http://10.17.1.66:3001/
scope: 复跑 regression_registry.md 全部 12 个已登记资产对应的 archive/ 归档脚本，统一 --base-url=http://10.17.1.66:3001
stop_at: final_report
exploration_driver: none
diagnostic_driver: none
forbidden: 全量探索、page-map-sync、改断言、上传 test_images/ 以外素材
assets: 账号按各 data/*.yaml 与 PROJECT.md；素材 test_images/；环境 http://10.17.1.66:3001/
assumptions:
  - 用户要求“跑所有已归档的回归脚本”，取 registry 每行的 Archive 列路径，共 12 个脚本。
  - 统一使用 --base-url=http://10.17.1.66:3001（覆盖脚本默认环境）；单个脚本失败不阻断后续，跑完整轮。
  - 稳定回归不做全量探索；selector/页面差异才局部回退，本轮仅记录不修脚本。
  - 首轮按 archive/ 副本执行时发现 7/12 早期归档脚本素材路径按脚本目录解析，在 archive/ 下不可独立复跑（非产品缺陷）；改按 registry Tests 列（当前可执行回归脚本）执行并保留 Test/Archive 双列于 summary.json。
artifacts:
  logs: artifacts/2026-09-14_stable_regression_all_archived/regression/
  summary: artifacts/2026-09-14_stable_regression_all_archived/regression/summary.json
  sync: artifacts/2026-09-14_stable_regression_all_archived/sync.md (confirmed)
  impl: artifacts/2026-09-14_stable_regression_all_archived/impl.md
  review: artifacts/2026-09-14_stable_regression_all_archived/review.md
  page_maps_drift:
    - page_map/pokecut/mobile_home_v2.yaml
    - page_map/pokecut/home_v7.yaml
    - page_map/pokecut/batch_v3.yaml
    - page_map/pokecut/create_ai_tools_v2.yaml
  mcp_evidence: artifacts/2026-09-14_stable_regression_all_archived/evidence/mcp_drift_20260914/
  allure_results: reports/allure-results-regression
  allure_report: reports/allure-report-regression
next_step: completed
blockers: []
---
# 调度历史
- 2026-09-14 15:41:07 orchestrator route: stable_regression / run all archived scripts registered in artifacts/regression_registry.md
- 2026-09-14 15:41:07 orchestrator step: 用户指定 --base-url=http://10.17.1.66:3001
- 2026-09-14 17:07:15 orchestrator run_registry_regression finished: 174 用例 161 passed / 10 failed / 3 skipped，总耗时约 75.4 分钟
- 2026-09-14 17:07:15 orchestrator wrote report.md + summary.json；allure-report-regression 生成；8123 指向回归报告
- 2026-09-14 17:07:15 orchestrator done status=completed artifacts/.current_task cleared
- 2026-09-14 18:06:37 orchestrator route: stable_regression 局部回退 -> page-map-sync drift round（driver=playwright_mcp_only）
- 2026-09-14 18:06:37 page-map-sync wrote sync.md status=pending_review + page_map v_next x4；bug_candidates=0
- 2026-09-14 18:06:37 orchestrator gate:sync_review waiting_user
- 2026-09-14 20:58:03 orchestrator archive: wrote archive.md / archive_cleanup_manifest.md / archive_cleanup_result.md；registry 已更新；状态置 archived
