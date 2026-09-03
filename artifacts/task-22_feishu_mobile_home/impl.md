---
task_id: task-22_feishu_mobile_home
agent: test-writing
status: completed
inputs:
  - artifacts/task-22_feishu_mobile_home/cases.md (confirmed)
  - page_map/pokecut/mobile_home_v1.yaml
outputs:
  test_file: tests/test_mobile_home.py
  data_file: null
  collect_only: 38 tests collected, 0 errors/warnings
  self_run: 37 passed, 1 skipped (TC-MH-L3-004 blocked_by_bug)（matrix run，含 Layer/标题修正后）
regression_candidate:
  eligible: true
  reason: 移动端首页为存量功能，已产出可复用脚本与版本化 page_map。
  suggested_tests: [tests/test_mobile_home.py]
  suggested_archive: page_map/pokecut/mobile_home_v1.yaml + cases.md + sync.md
  registry_key: pokecut_mobile_home_v3
next_agent: review
---

# 实现摘要

- 新增 `tests/test_mobile_home.py`，覆盖 confirmed cases.md 的 21 条用例（参数化后 38 个测试节点）。
- 使用独立移动端 context（390x844、iPhone UA、has_touch、deviceScaleFactor=3、en-US），保证移动端布局与文件选择器拦截。
- 上传全部走真实按钮 + `page.expect_file_chooser()` + `test_images/` 现有素材。
- 底部导航 Pricing 因 staging DEBUG 浮层遮挡，使用 JS click 规避。
- TC-MH-L3-004 因首页登录弹层提交无反应（blocked_by_bug）标记 skip，不弱化断言。

## 自修日志
- round 1：`test_mobile_home_structure` 底部导航 Upload 项断言用 `filter(has=...)` 误判（icon-only 按钮无文本子节点）。改为 `nav.locator("button[aria-label='...']").count()==1` 后通过。
- round 2：用户指出 Allure 缺 L1~L6 分层——补充 `@allure.label("layer")`、`@allure.title("<case_id> [<Layer>] <标题>")`，参数化用例用 `allure.dynamic.title` 带实际值；重跑 matrix 并重新生成报告。

## 命令与结果
- `python -m pytest tests/test_mobile_home.py --collect-only -q` → 38 tests collected, 0 errors/warnings。
- `python -m pytest tests/test_mobile_home.py -q` → 37 passed, 1 skipped in ~399s。

## 截图覆盖
- 通过 `conftest.py` 的 allure_screenshot 自动在用例结束态附加截图；上传/导航类用例在关键态已通过自动截图留证。
