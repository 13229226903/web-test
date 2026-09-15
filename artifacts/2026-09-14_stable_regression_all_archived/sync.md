---
task_id: 2026-09-14_stable_regression_all_archived
agent: page-map-sync
status: pending_review
round: drift_reexplore_20260914
task_type: stable_regression
exploration_driver: playwright_mcp_only
diagnostic_driver: none
inputs:
  failures: artifacts/2026-09-14_stable_regression_all_archived/report.md（10 条失败）
  user_note: 用户确认「实际页面没问题，可能是原脚本有问题」；/create 促销弹窗需脚本处理
outputs:
  page_maps:
    - page_map/pokecut/mobile_home_v2.yaml
    - page_map/pokecut/home_v7.yaml
    - page_map/pokecut/batch_v3.yaml
    - page_map/pokecut/create_ai_tools_v2.yaml
  evidence: artifacts/2026-09-14_stable_regression_all_archived/evidence/mcp_drift_20260914/
bug_candidates: 0
next_agent: test-writing
---

# sync.md — 全量回归失败项的漂移复探（2026-09-14）

## 1. 探索摘要

- 触发：registry 全量稳定回归 10 条失败；用户判定「页面实际正常，疑似原脚本漂移」，按 stable_regression 局部回退，**只复探漂移点，不做全量探索**。
- 驱动：Playwright MCP（`http://127.0.0.1:8931/mcp`，`_explore/mcp_drive_http.py` 驱动）；未启用 Chrome DevTools MCP。
- 环境：测试服 `http://10.17.1.66:3001/en`；移动端 390x844 + iPhone UA（is_mobile）；PC 1920x1080；匿名 + VIP `450832596@qq.com`（仅 batch 删除态需登录）。
- 结论：**4 处漂移、0 个产品缺陷**。原 10 条失败 = 4 类脚本/选择器漂移（9 条）+ 1 类测试服后端环境问题（2 条 `-1002`，此前已确认）。

## 2. 页面覆盖矩阵

| # | 页面 / 状态 | 探索点 | 结论 | 证据 |
|---|---|---|---|---|
| 1 | 移动端首页 hero（390x844） | `section.mobile-home-agent-hero` 是否存在、模型入口文案 | covered：section 存在；入口按钮文案 = **Auto**（原 Pokecut Pro） | `mobile_home_hero.png` |
| 2 | 移动端首页 模型弹层 | 点击模型入口 → 弹层选项 | covered：弹层正常打开，含 Pokecut Pro / ChatGPT Image 2.0 / Nano Banana / Nano Banana 2 / Seedream4.0 | `mobile_model_menu.png` |
| 3 | 移动端首页 effect 模板卡 | 原用例入口 “Butt” | covered：**Butt 不存在**（全页检索仅 `button`/i18n key 子串命中）；等价卡 `img[alt="Slim"]` 点击 → file chooser → `/create/edit?pid=` 成功 | `mobile_template_card_click.png` |
| 4 | PC 首页 hero 模型入口（1920x1080） | 模型按钮文案与菜单 | covered：`button.cinematic-model` 文案 = **Auto**；点击展开模型菜单，再点收起 | `pc_home_model_menu_open.png` |
| 5 | PC 首页 Prompt settings | `button[aria-label="Prompt settings"]` | covered：仍存在（count=1） | `pc_home_after_clicks.png` |
| 6 | Batch 批量编辑页 删除态（VIP） | 删除按钮文案 | covered：删除态按钮 = Cancel / Select All / **Delete** / DEBUG；全页无 “Delect” | `batch_delete_mode.png` |
| 7 | /create 入口页（全新匿名会话） | 促销弹窗与入口可点性 | covered：`.purchase-gift-modal` 遮挡 “Start from a Photo”；连点 close **两次**后弹窗数 0、入口恢复可点 | `create_promo_popup.png`、`create_after_close2.png`、`create_close_sequence.png` |

## 3. 需求差异（漂移对照）

| # | 项 | 原脚本预期 | 实测现状 | diff_type | 处置建议（下游 test-writing） |
|---|---|---|---|---|---|
| 1 | 移动端 hero 模型入口 | `section.mobile-home-agent-hero button` + `has_text="Pokecut Pro"` 可见 | 入口文案为 **Auto**（默认模型改为 Auto；Pokecut Pro 降级为弹层选项） | 脚本漂移 | L1-002 改为断言模型入口存在（用 `Auto`/`button` 结构或 aria），不断言具体模型名 |
| 2 | 移动端模型弹层 | 点击 `has_text="Pokecut Pro"` 打开弹层 | 点击 **Auto** 可正常打开弹层，选项齐全 | 脚本漂移 | L2-003 改为点击 `section.mobile-home-agent-hero button:has-text("Auto")` |
| 3 | 移动端 effect 模板卡 | `get_by_role("button", name="Butt")` | 无 “Butt” 入口；`img[alt="Slim"]` 卡片可完成「点击→选择文件→进入 /create/edit」 | 脚本漂移 | L2-010 改用 `img[alt="Slim"]`（或同族模板卡）作为上传触发 |
| 4 | PC 首页模型入口 | `data.pokecut_pc_home_v6.yaml: hero.model_button = "Pokecut Pro"` + `.cinematic-popup` | 模型按钮文案 = **Auto**；选择器 `button.cinematic-model`；`.cinematic-popup` 已不是菜单容器 | 脚本漂移 | data 改为 `model_button: "Auto"`（或直接用 `button.cinematic-model`）；菜单断言改用菜单内文案 |
| 5 | Batch 删除按钮 | 断言/点击 `name="Delect"`（验证拼写 bug 修复） | 文案已修复为 **Delete**；无 Delect | 脚本漂移（bug 已修复） | L1-007 断言改为 “文案为 Delete（拼写已修复）”；L2-011/L2-012 点击 `name="Delete"` |
| 6 | /create 入口 | 直接点 “Start from a Photo” | 全新匿名会话会弹 `.purchase-gift-modal` 促销层，遮罩拦截点击；连点 `img[src*="colos_pop_btn_close"]` 两次后恢复可点 | 脚本缺口 | 进入 /create 后增加弹窗兜底关闭（最多 3 次循环），再点击入口 |
| 7 | Enhance Standard 4K/8K | 提交成功出结果 | 测试服后端返回 `-1002`（用户已确认临时环境问题） | 环境 | 服务恢复后复跑；脚本无需改 |

## 4. 关键发现与下游注意事项

1. **/create 促销弹窗必须连点两次**：第 1 次关闭 “$1 USD 限时优惠” 层，第 2 次关闭随之出现的 “Premium Plan / Credits Purchase” 定价层；否则入口始终被 `.purchase-gift-modal__content` 拦截。建议统一封装为脚本前置步骤。
2. **默认模型已变更为 Auto**：移动端与 PC 首页 hero 的模型入口都显示 Auto，Pokecut Pro 仍作为可选项存在于模型列表 → 断言应基于「入口存在 + 弹层选项齐全」，不要绑定具体模型名。
3. **Batch 的 Delect 拼写缺陷已修复**：`L1-007` 这类「验证 bug 修复」用例在修复后必须同步改断言方向（改为断言正确文案），否则会持续失败。
4. **移动端 effect 模板卡命名已变化**：原 “Butt” 入口消失，模板卡集合为 GPT-Image2 / Try-On / Slim / Lofi / Body Sculpt / Muscle / Flux Gen / Flash Effect / Young / Suit / Spiderman / Proportion Edit / Dark Tan / Smile Lines / Gold Tan / Jelly Photo Filter / High Crown；`Slim` 已实测可完成上传进画布。
5. **页面地图版本**：`mobile_home_v1 → v2`、`home_v6 → v7`、`batch_v2 → v3`、`create_ai_tools → v2`（均保留历史版本）。

## 5. 版本差异摘要

| page_map | 变更 |
|---|---|
| `mobile_home_v2.yaml` | 新增 `drift_20260914`：hero 模型入口文案、弹层选项、模板卡现状与 `Slim` 等价入口 |
| `home_v7.yaml` | 新增 `drift_20260914`：`button.cinematic-model` 入口与 Auto 文案、菜单容器变化 |
| `batch_v3.yaml` | 新增 `drift_20260914`：删除态按钮文案改为 Delete |
| `create_ai_tools_v2.yaml` | 新增 `drift_20260914`：促销弹窗选择器与两次关闭时序 |

## 6. bug_candidates

- 无。本轮复探 0 个产品缺陷；此前 BUG-REG-001~008 均归因为脚本漂移/脚本缺口，BUG-REG-009/010 为测试服环境问题。
- 说明：`report.md` 中的 Bug 提报章节需按本轮结论改写为「脚本漂移修复清单」，由 test-writing 阶段落地。
