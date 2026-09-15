# Bug Candidate — 移动端画布生图面板默认模型与首页不一致（应为 Auto，实际 Nano Banana 2 Lite）

- 任务：2026-09-14_stable_regression_all_archived（2026-09-15 追加）
- 模块：Pokecut 移动端（390x844）→ 底部导航 Generate → 画布内「生图面板」
- 优先级：P1（默认模型直接决定出图模型与计费档位）
- 对应用例：	ests/test_mobile_home.py::TestL2Interactions::test_l2_020_bottom_nav[generate]（L2-020 — Generate）
- 环境：测试服 http://10.17.1.66:3001/en，移动端 iPhone UA

## [步骤]

1. 移动端打开首页 /en
2. 点击底部导航 **Generate**
3. 等待进入画布（/create/edit?pid=<uuid>）并展开生图面板
4. 读取生图面板模型入口的当前文案

## [结果]

- 生图面板模型入口文案为 **Nano Banana 2 Lite**（utton > span.whitespace-nowrap）。
- 面板内不存在 Auto：document.body.innerText.includes('Auto') === false。
- 断言 ctual_model == "Auto" 失败：AssertionError: 生图面板默认模型应为 Auto，实际为 Nano Banana 2 Lite。
- 对比：**同一站点首页 hero 的模型入口默认是 Auto**（2026-09-14 复探已确认），即首页与画布生图面板默认模型不一致。

## [期望]

- 进入生图面板时应默认选中 **Auto**（与首页 hero 默认一致）。

## 截图

- MCP 复探：rtifacts/2026-09-14_stable_regression_all_archived/evidence/mcp_drift_20260915/canvas_generate_panel2.png
- 用例失败截图：Allure eports/allure-results-mobile-fix 中 L2-020_generate 附件（shot(page, "L2-020_generate")）