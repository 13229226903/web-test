---
task_id: 2026-09-21_mobile_home_drift_fix
agent: review
status: completed
inputs:
  impl: artifacts/2026-09-21_mobile_home_drift_fix/impl.md
  sync: artifacts/2026-09-21_mobile_home_drift_fix/sync.md
  page_map: page_map/pokecut/mobile_home_v3.yaml
  diff:
    - tests/test_mobile_home.py
    - archive/mobile_home/test_mobile_home.py
outputs:
  verdict: pass
  blocking_issue_count: 0
  suggestion_count: 2
  next_agent: test-writing
---

# review.md — 移动端首页漂移修复

## Blocking Issues

无。

## Suggestions

1. `RATIO_OPTIONS_BY_MODEL` 当前只有 `Nano Banana 2 Lite`。后续若要覆盖其他模型的比例列表，应继续按模型补充映射，不要复用当前集合。
2. `L2-003` 仍沿用历史“模型选项齐全”的部分选项断言；本轮未扩大范围。若后续用户要求完整覆盖模型菜单，应基于 page_map v3 的 10 项列表补全。

## Checked Items

- 未删除或弱化原断言；`L2-004` 从部分包含断言升级为默认模型对应的完整有序集合断言。
- selector 使用 `role` + `aria-label` 与稳定文本；未新增 hash class、`:nth-child` 或位置 XPath。
- 默认模型 `Nano Banana 2 Lite` 已在 `.mobile-home-agent-hero` 范围内定位，避免命中弹层同名按钮。
- `Slim` 上传仍断言 file chooser 和 `/create/edit?pid=*`，未只验证元素存在。
- 底部 Generate 仍断言 `/create/edit?pid=*` 和实际默认模型，未削弱导航结果。
- `tests/test_mobile_home.py` 与 `archive/mobile_home/test_mobile_home.py` SHA256 一致。
- `page_map/pokecut/mobile_home_v3.yaml` YAML 解析通过，比例入口为 `covered`，实际 8 项已登记。
- 归档副本 collect-only 38/0，最终全量自跑 38 passed in 460.92s；无 failed / skipped。
- 截图证据存在，改动范围未超出用户确认的漂移点。