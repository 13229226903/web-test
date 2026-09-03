---
task_id: task-22_feishu_mobile_home
agent: review
status: completed
inputs:
  - artifacts/task-22_feishu_mobile_home/impl.md
  - tests/test_mobile_home.py
  - artifacts/task-22_feishu_mobile_home/cases.md
  - page_map/pokecut/mobile_home_v1.yaml
outputs:
  verdict: pass
  blocking_issue_count: 0
  suggestion_count: 3
  next_agent: test-writing(report-output)
---

# review.md

## Blocking Issues
- 无。

## Suggestions
1. 预期文案/URL 目前在用例参数中硬编码，建议后续抽取到 `data/pokecut_mobile_home.yaml`，与 data 层约定一致。
2. 人像 tab 测试使用 `#home-mobile-portrait-tab-*` 稳定 id，建议将该 id 补进 `page_map/pokecut/mobile_home_v1.yaml` 的 `tabs.portrait_tabs`，提升可追溯性。
3. 比例入口 selector 依赖 Tailwind 任意类 `[class*='size-[2.625rem]']`，如产品侧有 aria-label/data-testid，建议改用稳定属性。

## Checked Items
- 断言字段：已覆盖主要动作结果与 URL/可见态；未删断言、未弱化 expected。
- 文本断言：以包含关系为主，避免精确格式漂移。
- selector：无 hash class、`:nth-child`、位置 XPath；底部导航/功能卡/agent 入口均用 role/aria/稳定 id。
- 架构：`tests/test_mobile_home.py`，中文注释；移动端独立 context。
- 数据：上传素材仅 `test_images/`；TC-MH-L3-004 因登录 bug 标 skip（非弱化断言）。
- 引用：impl.md 的 test_file 与 git diff 一致；page_ref 指向的 page_map 元素存在。
- 报告层级与截图：使用 Allure epic/feature/story + `@allure.label("case_id")`；conftest 自动在通过/失败态附截图，满足每条用例至少 1 截图。
