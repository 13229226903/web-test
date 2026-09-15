---
task_id: 2026-09-14_stable_regression_all_archived
agent: orchestrator
status: completed
task_type: stable_regression
base_url: http://10.17.1.66:3001
total: 174 / passed: 161 / failed: 10 / skipped: 3
duration: 2026-09-14 17:07
---

# 稳定回归报告 — registry 全部登记资产 @ http://10.17.1.66:3001

## 结果总览

| # | 任务（脚本） | registry 状态 | 结果 | 耗时 |
|---|---|---|---|---|
| 1 | `tests/test_pokecut_portrait_detector.py` | stable_regression | ✅ 14 passed | 318.61s |
| 2 | `tests/test_ai_image_text_enhancer_experiment.py` | stable_regression | ⚠️ 16 passed, 2 skipped | 787.80s |
| 3 | `tests/test_infinite_canvas_text_layer_v2.py` | stable_regression | ✅ 6 passed | 300.08s |
| 4 | `tests/test_mobile_home.py` | stable_regression | ❌ 34 passed, 3 failed, 1 skipped | 434.92s |
| 5 | `tests/test_help_page.py` | stable_regression | ✅ 11 passed | 190.06s |
| 6 | `tests/test_detection_ui_seo_l6.py` | stable_regression | ✅ 2 passed | 173.23s |
| 7 | `tests/test_pokecut_pc_home_v6.py` | stable_regression | ❌ 16 passed, 1 failed | 372.36s |
| 8 | `tests/test_pokecut_pc_batch_v1.py` | pending_fix | ❌ 13 passed, 3 failed | 382.50s |
| 9 | `tests/test_old_canvas_insert_panel_v3.py` | stable_regression | ✅ 24 passed | 580.38s |
| 10 | `tests/test_old_canvas_text_panel_v1.py` | stable_regression | ✅ 13 passed | 388.36s |
| 11 | `tests/test_old_canvas_sticker_panel_v1.py` | stable_regression | ✅ 9 passed | 205.08s |
| 12 | `tests/test_infinite_canvas_enhance_v4.py` | pending_fix | ❌ 3 passed, 3 failed | 389.66s |

- 合计：**161 通过 / 10 失败 / 3 跳过（共 174）**，串行总耗时约 75.4 分钟。
- Allure：`reports/allure-report-regression`（页面统计：passed 161 / failed 3 / broken 7 / skipped 3）。
- 原始日志：`artifacts/2026-09-14_stable_regression_all_archived/regression/<name>.log`，结构化结果 `regression/summary.json`。

## 失败明细与原因

### 1. `test_mobile_home.py`（34 passed / 3 failed / 1 skipped）

| 用例 | 原因摘要 |
|---|---|
| `test_l1_002_hero_copy` | `section.mobile-home-agent-hero button` + 文案 “Pokecut Pro” 定位 5s 内不可见（element not found） |
| `test_l2_003_model_popover` | 同 selector 点击 15s 超时 |
| `test_l2_010_effect_template` | `get_by_role("button", name="Butt")` 定位超时 |

### 2. `test_pokecut_pc_home_v6.py`（16 passed / 1 failed）

| 用例 | 原因摘要 |
|---|---|
| `test_l2_008_prompt_popups` | `button:has-text("Pokecut Pro")` scroll_into_view 30s 超时 |

### 3. `test_pokecut_pc_batch_v1.py`（13 passed / 3 failed，registry 已标 pending_fix）

| 用例 | 原因摘要 |
|---|---|
| `test_l1_007_delete_label_bug` | `get_by_role("button", name="Delect")` 超时（registry Notes 已登记的 Delete 文案错拼已知项） |
| `test_l2_011_delete_flow` | 同 “Delect” 按钮定位超时 |
| `test_l2_012_download_flow` | 同 “Delect” 按钮定位超时 |

### 4. `test_infinite_canvas_enhance_v4.py`（3 passed / 3 failed，registry 已标 pending_fix）

| 用例 | 原因摘要 |
|---|---|
| `test_l5_001_resolution_default_matrix_and_8k_uncompressed` | `upload_via_create` 点击 “Start from a Photo” 卡片 20s 超时：**页面弹出 VIP $1 USD 限时优惠弹窗，遮罩拦截入口点击**（本轮新失败，上轮矩阵为 passed） |
| `test_l6_002_standard_portrait_text_matrix` | 提交 Standard 4K 后端返回 `-1002`（测试服临时问题，已知） |
| `test_l6_003_8k_routes` | 提交 Standard 8K 后端返回 `-1002`（同上） |

## 归因分组

1. **默认模型变更导致首页入口变化（4 条）**：`mobile_home` 3 条 + `pc_home_v6` 1 条均指向首页 hero 区 `Pokecut Pro` 按钮缺失。已确认根因为**新增模型后默认模型改为 “Auto”**（hero 区模型下拉默认 Auto；Pokecut Pro 变为模型列表中的一项），属产品变更未同步到用例。
2. **Batch 页 “Delect” 按钮（3 条）**：与 registry 已登记的 Delete 文案错拼已知项同源；`pending_fix` 状态保持。
3. **测试服后端 `-1002`（2 条）**：`L6-002` / `L6-003` 与上轮一致，非产品缺陷，服务恢复后复跑。
4. **VIP 营销弹窗遮挡入口（1 条）**：`L5-001` 在 /create 点 “Start from a Photo” 卡片被 VIP $1 USD 限时优惠弹窗遮罩拦截（已复现并截图），属新暴露阻塞。

## 归档副本可执行性发现

- 首轮按 registry `Archive` 列（`archive/**`）执行时出现大面积失败（`portrait_detector` 1 failed + 13 errors、`tool_pages` 17 failed），根因为早期归档副本章节将素材路径按脚本所在目录解析（`archive/test_images/...`），在 `archive/` 下不存在。
- 分布：12 个归档副本中 **5 个可独立复跑**（`infinite_canvas_enhance` / `infinite_canvas_insert_panel` / `infinite_canvas_sticker_panel` / `infinite_canvas_text_panel` / `pc_batch`，已按 `test_images/` 上溯定位仓库根），**7 个不可**（`portrait_detector` / `tool_pages` / `infinite_canvas` / `mobile_home` / `help_center` / `detection_ui` / `pc_home`）。
- 处置：本轮改按 registry `Tests` 列（字段定义即“当前可执行回归脚本”）统一复跑，`summary.json` 同时保留 `tests` 与 `archive` 双列便于追溯。
- 建议：后续归档时统一使用 `_repo_root()` 式仓库根定位，保证归档副本可独立复跑。

## 交付与证据

- 运行器：`run_registry_regression.py`（从 registry 解析任务、串行执行、逐脚本落日志与 summary）
- 控制台日志：`regression/runner_console.log`
- 逐脚本日志：`regression/*.log`
- 结构化结果：`regression/summary.json`
- Allure 结果/报告：`reports/allure-results-regression`、`reports/allure-report-regression`
- 服务：http://localhost:8123/index.html （指向 `reports/allure-report-regression`）

## Bug 提报

- 本轮 10 条失败已按模板（标题 / 模块 / 类型 / 优先级 / 前置 / 步骤 / 结果 / 期望 / 截图）整理为 **BUG-REG-001 ~ BUG-REG-010**：`bug_report_regression_20260914.md`。
- 对应关系：4 条=默认模型变更（首页入口）；3 条=Batch 删除控件文案/可访问名（已知 “Delect” 项同源）；1 条=/create 被 VIP 限时优惠弹窗遮挡入口；2 条=测试服后端 `-1002`（环境类，非产品缺陷）。
- 失败现场截图：`shots/failure_capture/`（含移动端 hero、PC 首页失败页、Batch 编辑页、/create 弹窗遮挡、Enhance 失败页）。
