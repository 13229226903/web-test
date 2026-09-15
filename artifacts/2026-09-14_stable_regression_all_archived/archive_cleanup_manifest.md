---
task_id: 2026-09-14_stable_regression_all_archived
agent: orchestrator
status: pending_cleanup
delete_count: 0
keep_count: 112
created_at: 2026-09-14 20:58:03
---

# archive_cleanup_manifest — registry 全量回归 + 漂移修复

## 结论：无待删除项（0）

本轮为 stable_regression 漂移修复轮，目录内所有文件均可追溯到正式产物或被引用证据：

- 版本化 artifact：state.md / progress.log / journal.jsonl / sync.md / impl.md / review.md
- 报告：report.md（失败归因）、regression/summary.json + regression/*.log（首次失败 run 与修复后复跑的原始证据）
- 复探证据：evidence/mcp_drift_20260914/（PNG + log_*.txt，sync.md 逐条引用）
- 历史截图：shots/failure_capture/（bug 草稿引用）
- 驱动脚本：run_registry_regression.py / capture_*.py / probe_*.py（可复跑）
- MCP 驱动输入 req_*.jsonl 体积小且可重新生成，一并保留以保持复探链路完整

## 待删除清单

- 无