---
task_id: 2026-09-14_stable_regression_all_archived
agent: test-writing
status: completed
inputs:
  sync: artifacts/2026-09-14_stable_regression_all_archived/sync.md (confirmed)
  page_maps: [page_map/pokecut/mobile_home_v2.yaml, home_v7.yaml, batch_v3.yaml, create_ai_tools_v2.yaml]
outputs:
  test_files: [tests/test_mobile_home.py, tests/test_pokecut_pc_batch_v1.py, tests/test_infinite_canvas_enhance_v4.py, tests/test_infinite_canvas_text_layer_v2.py, tests/helpers_create_entry.py]
  data_files: [data/pokecut_pc_home_v6.yaml, data/pokecut_pc_batch_v1.yaml]
  self_run: 8 条漂移用例全部定向自跑通过（mobile x3 / batch x3 / enhance L5-001 / pc_home L2-008）
regression_candidate:
  eligible: false
  reason: 局部漂移修复，待 PC 首页 L2-008 处理完后整包复跑再评估
next_agent: review
created_at: 2026-09-14 18:17:30
---

# impl.md — 回归漂移修复（2026-09-14）

## 修复项

| # | 用例 | 修复内容 | 结果 |
|---|---|---|---|
| 1 | mobile L1-002 | 模型入口断言 Pokecut Pro → Auto（page_map mobile_home_v2） | passed |
| 2 | mobile L2-003 | 点击入口改用 `button:has-text('Auto')`，弹层选项断言不变 | passed |
| 3 | mobile L2-010 | 入口 `img[alt='Slim']` 模板卡（原 Butt 不存在）；缩略图为 invisible 叠加层，用 `expect_file_chooser` + `force=True` 点击 | passed |
| 4 | batch L1-007 | 删除按钮文案断言 Delect → Delete（缺陷已修复，改回归断言方向） | passed |
| 5 | batch L2-011 | 点击 `name='Delete'` | passed |
| 6 | batch L2-012 | 点击 `name='Delete'` | passed |
| 7 | enhance L5-001 | 新增 `tests/helpers_create_entry.py::dismiss_create_promo`，在 `upload_via_create` 中先关闭 /create 的 VIP 促销+定价弹窗（连点 2 次） | passed |

## 自跑命令与结果

``text
python -m pytest tests/test_mobile_home.py tests/test_pokecut_pc_batch_v1.py tests/test_infinite_canvas_enhance_v4.py -q -k "test_l1_002_hero_copy or test_l2_003_model_popover or test_l2_010_effect_template or test_l1_007_delete_label_bug or test_l2_011_delete_flow or test_l2_012_download_flow or test_l5_001_resolution_default_matrix_and_8k_uncompressed" --base-url=http://10.17.1.66:3001 --alluredir=reports/allure-results-drift-fix --clean-alluredir
=> 6 passed, 1 failed（L2-010 卡片点击方式）

修正后：
python -m pytest tests/test_mobile_home.py -q -k "test_l2_010_effect_template" --base-url=http://10.17.1.66:3001
=> 1 passed, 37 deselected
``

## 未完成项（需再走一次 page-map-sync 局部复探）

- **pc_home L2-008 模型菜单**：已确认入口为 `button.cinematic-model`（文案 Auto）并改好 data；但 MCP 复探中点击该按钮未观察到模型菜单展开（`.cinematic-popup` count=0、无 `role=listbox/option`、未见模型名面板），
  **展开机制（hover / 二次点击 / 弹层新容器）未确认**，故本用例暂未改断言，保持失败待复探。
- **其它进入 /create 的旧画布脚本**（insert panel v3 / text panel v1 / sticker panel v1）尚未接入 `dismiss_create_promo`；这些脚本入口为 zh-CN 会话，需在下次回归复跑时确认是否同样受促销弹窗影响。
``
## 补探记录（pc_home L2-008，已收敛）

- MCP 复探证据（`evidence/mcp_drift_20260914/log_S.txt`、`pc_model_dispatch.png`）：入口为 `button.cinematic-model`（文案 Auto，坐标 y=1115 在首屏下方）；
  - 坐标点击（mouse.click 按钮中心）→ 无菜单；
  - `dispatchEvent(new MouseEvent('click'))` → `.cinematic-popup` count=1，内容 `Nano Banana / Better visuals & overall image quality.` → **菜单确实可打开**。
- 已把用例改为 `page.locator("button.cinematic-model").first` + `dispatch_event("click")` + 等待 2.5s，但 pytest 自跑仍失败（`.cinematic-popup` 不可见）。
  - 差异点：MCP 成功序列为「textbox 点击 → 坐标点击 → dispatchEvent」；用例序列为「textbox(name=AI image prompt) 点击 → scroll_into_view → dispatchEvent」。
  - 未收敛原因假设：焦点/滚动时序，或 popup 需要一次真实 click 后才响应 dispatchEvent。
- 收敛结果：最小序列 = `textbox 点击 → scrollIntoView → dispatchEvent("click")`（**菜单是 toggle，第二次 dispatch 会关闭**）；用例补充 `wait_for(state="visible")` + 水合等待，并用「未展开才 dispatch」循环兜底 → 模型菜单断言通过。
- 继续推进后发现第二处漂移：设置面板标签由 `Output Resolution:` 变为 `Output Ratio:` → 更新 `data/pokecut_pc_home_v6.yaml::settings_options`。
- 最终：`python -m pytest tests/test_pokecut_pc_home_v6.py -q -k "test_l2_008_prompt_popups"` → **1 passed**。
