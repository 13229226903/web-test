---
task_id: 2026-09-21_mobile_home_drift_fix
agent: page-map-sync
status: confirmed
round: selector_drift_20260921
task_type: stable_regression
repair_scope: selector_drift
gate_exemption: 用户明确要求指定元素漂移“以实际的为准，需要修改断言”，并追加确认 L2-004 不同模型比例不同；授权直接进入 test-writing
exploration_driver: playwright_mcp_only
diagnostic_driver: none
inputs:
  failures: artifacts/2026-09-20_stable_regression_archived_all/regression/test_mobile_home.log
  page_map: page_map/pokecut/mobile_home_v2.yaml
  user_note: 模型入口、底部导航 Generate、比例列表属于元素漂移，以实际为准；Slim effect 模板卡实际存在；不同模型有不同的比例
outputs:
  scanned_pages:
    - http://10.17.1.66:3001/
    - http://10.17.1.66:3001/create/edit?pid=<uuid>
  page_map_versions:
    - page_map/pokecut/mobile_home_v3.yaml
  coverage_gates:
    - L1-002
    - L2-003
    - L2-010
    - L2-004
    - L2-020-generate
  bug_candidates: 0
  skipped: []
  specs_updated: []
next_agent: test-writing
created_at: 2026-09-21 09:28:00
---

# sync.md — 移动端首页 selector 漂移局部复探（2026-09-21）

## 1. 探索摘要

- 触发：2026-09-20 归档回归中移动端首页 5 条失败；用户确认模型入口、底部导航 Generate、比例列表为元素漂移，以实际为准，并确认 Slim effect 模板卡实际存在。
- 模式：`stable_regression` 局部回退，`repair_scope=selector_drift`；只复探失败相关页面与状态，不做全量探索。
- 驱动：当前会话 Playwright MCP preflight 通过；环境 `http://10.17.1.66:3001/`，390x844 viewport，匿名态。
- 结论：4 个指定失败点均为脚本 selector / expected 漂移，页面功能正常，0 个 bug candidate。
- 比例列表按模型维度处理：当前默认模型 `Nano Banana 2 Lite` 的实际比例为 `1:1 / 3:4 / 4:5 / 4:3 / 9:16 / 16:9 / 2:3 / 3:2`；用户已明确不同模型比例不同，测试应以当前模型实际集合为准。

## 2. 页面覆盖矩阵

| # | 页面 / 状态 | 探索点 | 结论 | 证据 |
|---|---|---|---|---|
| 1 | 移动端首页 hero | 默认模型入口 | covered：入口文案/按钮文本实际为 `Nano Banana 2 Lite`，不再为 `Auto` | `evidence/hero_nano_banana_2_lite.png` |
| 2 | 移动端首页模型弹层 | 点击实际默认模型入口 | covered：弹层正常打开，包含 `Auto`、ChatGPT Image 2.0、Nano Banana、Nano Banana 2、Nano Banana 2 Lite、Nano Banana Pro、Pokecut Pro、Seedream 5.0 Lite、Seedream 5.0 Pro、Seedream4.0 | `evidence/hero_model_menu.png` |
| 3 | 移动端首页 AI Templates | effect `Slim` 模板卡 | covered：`div[role='button'][aria-label='Slim']` 实际存在；点击触发 file chooser，选择 `test_images/有人脸.JPG` 后进入 `/create/edit?pid=<uuid>` | `evidence/effect_slim_card.png`；MCP action/snapshot |
| 4 | 移动端首页底部导航 | `Generate` | covered：不触发 file chooser，进入 `/create/edit?pid=<uuid>`；生图面板默认模型按钮实际为 `Nano Banana 2 Lite` | `evidence/bottom_generate_nano_banana_2_lite.png` |
| 5 | 移动端首页 hero | 比例入口 | covered：当前默认模型 `Nano Banana 2 Lite` 实际可见 8 项为 `1:1 / 3:4 / 4:5 / 4:3 / 9:16 / 16:9 / 2:3 / 3:2`，无 `9:21`；用户确认比例随模型变化 | `evidence/ratio_options_nano_banana_2_lite.png`；MCP DOM 实测 |

## 3. 需求差异

| # | 项 | 原脚本预期 | 实测现状 | diff_type | 处置 |
|---|---|---|---|---|---|
| 1 | L1-002 默认模型入口 | `button` 文案含 `Auto` | 文案为 `Nano Banana 2 Lite` | selector / expected 漂移 | 修改为实际默认模型文本，仍保留可见性断言 |
| 2 | L2-003 模型入口展开 | 点击文案含 `Auto` 的按钮 | 点击 `Nano Banana 2 Lite` 可正常展开 | selector 漂移 | 修改点击入口，模型选项断言保持 |
| 3 | L2-010 effect 模板上传 | `img[alt='Slim']` | 实际卡片为 `div[role='button'][aria-label='Slim']`，图片 alt 为描述性文案 | selector 漂移 | 改用 role + aria-label，保留 file chooser 与画布跳转断言 |
| 4 | L2-020 底部 Generate | 画布默认模型应为 `Auto` | 实际为 `Nano Banana 2 Lite` | expected / selector 漂移 | 修改为实际默认模型文本，保留 URL 与模型存在断言 |
| 5 | L2-004 比例入口 | 需包含 `9:21` | 默认模型 `Nano Banana 2 Lite` 实际无 `9:21`，集合为 `1:1 / 3:4 / 4:5 / 4:3 / 9:16 / 16:9 / 2:3 / 3:2`；比例随模型变化 | selector / expected 漂移（用户已确认） | 绑定默认模型，断言实际 8 项完整集合，不保留旧 `9:21` |

## 4. 关键发现与下游注意事项

1. 首页模型默认值已由 `Auto` 切为 `Nano Banana 2 Lite`；模型弹层本身仍包含 `Auto`，因此不能再用 `Auto` 反推 hero 默认入口。
2. `Slim` 模板卡不是缺失：旧选择器 `img[alt='Slim']` 只匹配精确 alt，但卡片图片 alt 已变为描述性文本；稳定定位应使用卡片的 role + `aria-label`。
3. 底部导航 `Generate` 的交互链路未变：`/create/edit?pid=*`；变的是进入后默认模型文案。
4. 比例集合随模型变化；当前用例固定默认模型 `Nano Banana 2 Lite`，应同时校验默认模型与对应 8 项比例集合，不能用通用固定列表覆盖所有模型。
5. `page_map/pokecut/mobile_home_v3.yaml` 为增量版本，`v2` 及更早版本保留不覆盖。

## 5. 版本差异摘要

| page_map | 变更 |
|---|---|
| `mobile_home_v3.yaml` | 更新 hero 默认模型入口为 `Nano Banana 2 Lite`；更新 effect `Slim` 卡片 selector 为 `div[role='button'][aria-label='Slim']`；补充底部 Generate 实际默认模型与 URL 断言提示；将比例入口更新为默认模型对应的实际 8 项集合并标记 covered |