---
task_id: 2026-11-02_stable_regression_3002
agent: orchestrator
status: completed
current_step: regression_summary_done
execution_mode: codex_single_context
task_type: stable_regression
human_gates_pending: []
knowledge_context: null
handoff_status: null
agent_call_count:
  page-map-sync: 0
  test-case-design: 0
  test-writing: 0
  review: 0
  visual-review: 0
target_url: http://10.17.1.66:3002/
execution_note: codex_single_context（未用子代理）
created_at: 2026-11-02 10:05:46
artifacts:
  registry: artifacts/regression_registry.md
---
# 调度历史
- 2026-11-02 10:05:46 用户要求：在 http://10.17.1.66:3002/ 跑 regression_registry.md 里面的回归脚本。
- 轮次范围：registry 全部 stable_regression（17 条）；#25 PC Enhance 为 pending_fix，不跑。
- 执行顺序：按 registry 行序串行执行；结果目录 reports/allure-results-regression。
# 终态原因
# 重新开始
- 2026-11-02 10:23:45 用户要求切换域名到 http://10.17.1.66:3002/ 重跑；清空 3001 结果，重置 allure-results-regression，重新开始串行回归。

