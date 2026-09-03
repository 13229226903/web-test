---
task_id: 2026-08-31_pokecut_help_center
agent: test-writing
status: completed
inputs:
  - artifacts/2026-08-31_pokecut_help_center/cases.md (confirmed, 去重后 11 条 L1~L6)
  - artifacts/2026-08-31_pokecut_help_center/sync.md (confirmed)
  - page_map/pokecut/help_v2.yaml
outputs:
  test_file: tests/test_help_page.py
  data_file: null
  collect_only: 11 tests collected, no error/warning
  self_run: 11 passed, 0 failed in 187.80s
regression_candidate:
  eligible: true
  reason: 去重后 11 条用例全部通过，失败 0；帮助页为匿名内容页
  suggested_tests: tests/test_help_page.py
  suggested_archive: archive/help_center/test_help_page.py
  registry_key: 帮助中心（/help）
next_agent: review
---

# impl.md — 帮助中心（/help）自动化实现（去重后 11 条，L1~L6）

## 实现摘要
- 脚本 `tests/test_help_page.py`，按 confirmed cases 11 条设计，报告呈现 11 条用例（L1:1、L2:7、L3:1、L5:1、L6:1）。
- 标签/分类/计数类在单条用例内循环覆盖，不参数化展开，Allure 用例数与 cases.md 一致。
- L6-001 恢复为 smoke，走分类卡片入口（与 L2-002 左侧导航入口互补），保证 L1~L6 分层完整。
- 全部 `@pytest.mark.no_login`；策略 L1=regression、L2/L3/L5=full、L6=smoke。

## 自修日志
- round 1（14 条版）：26 passed（含参数化）。
- round 2（去重 10 条，参数化）：20 passed。
- round 3（去重 10 条，去参数化循环）：10 passed。
- round 4（去重 11 条，L1~L6 + L2-005 空态截图修正 + L6 恢复）：11 passed。

## 关键修正
- L2-005：新增空态截图步骤（点击 Submit a ticket 前截 `07搜索空态`），点击后再截 `07b工单弹窗`，修复空态无截图。
- 报告去参数化：标签/分类/计数类改单条内部循环，Allure 用例数 11 与 cases.md 一致。

## 命令与结果
- collect-only：`python -m pytest tests\test_help_page.py --collect-only -q` → 11 tests collected。
- self-run：`python -m pytest tests\test_help_page.py -q --tb=short --clean-alluredir` → 11 passed in 187.80s。
- 报告：`reports/report.html`；allure-report-matrix 已重新生成（11 条）。

## 报告路径与截图覆盖
- 每条用例步骤内截图；L2-005 含空态与弹窗两张截图；循环用例按实际值在步骤内截图。

## 待 review 备注
- 移动端分类卡片 selector 实测为 `help-v2-mobile-category-card`（page_map 记为 desktop 类名），代码已区分，建议后续 page-map-sync 修正。
