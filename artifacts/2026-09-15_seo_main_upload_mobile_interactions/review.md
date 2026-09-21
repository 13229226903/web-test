---
task_id: 2026-09-15_seo_main_upload_mobile_interactions
agent: review
status: completed
review_round: 2
inputs:
- artifacts/2026-09-15_seo_main_upload_mobile_interactions/impl.md
- tests/mobile/test_seo_main_upload_mobile_v1.py
- tests/mobile/conftest.py
- data/pokecut_seo_main_upload_mobile_interactions_v1.yaml
- artifacts/2026-09-15_seo_main_upload_mobile_interactions/cases.md
- page_map/pokecut/seo_upload_mobile/ (24 files)
- evidence/panel_timing_probe_v3.json / layer_selected_probe3/4.json / landing_selector_scan.json
outputs:
  verdict: pass
  blocking_issue_count: 0
  suggestion_count: 4
  next_agent: test-writing(report-output)
---

# 审查轮次

| 轮次 | 结果 | 结论 |
|---|---|---|
| R1 | `fail`（blocking=1） | B1：cases.md 预期「图片图层默认选中」未断言，`_image_layer_selected()` 为死代码且用通配 selector |
| R2 | **`pass`**（blocking=0） | B1 已修复：新增稳定 selector 取证 → 写 page_map → `_wait_for_selected_layer()` 真断言；R7 轮暴露的 2 条入口偶发（502 / 未触发上传）已在 R8 加固 |

# Blocking Issues

无。

**R1 B1 修复核对**：

- 取证：`evidence/layer_selected_probe3.json` 显示 `.choose-boder` = `2px dashed rgb(104,104,104)` 选中框（350×468）+ 4 个 `span.scale-point` 手柄（20×20、`border-radius 100%`、`cursor-*-resize`）；`layer_selected_probe4.json` 在 L2-014/018/021/023/024（含 de / zh-tw / th 三语种）复核一致。
- page_map：21 份 legacy_canvas 地图补 `states.after_upload.elements.selected_layer_frame`（`.choose-boder`）与 `selected_layer_handles`（`.choose-boder .scale-point`），均带 `explore_status: covered` + `evidence` 路径，24/24 YAML 可解析。
- 脚本：删除死代码 `_image_layer_selected()`（含 `[class*=...]` 通配），改为 `_wait_for_selected_layer()`（轮询等「选中框可见 + ≥4 手柄」）+ 两条断言（选中框与画布同量级 >200×200；手柄 ≥4）。断言为**新增**，未删除/弱化任何既有断言。

# Suggestions

1. [测试服稳定性，非阻塞] 全量 R7 轮出现 1 次落地页 **nginx 502**（`data/screenshots/L2-004_failure.png` 可复现判读）。现已在 `_open_target()` 命中 502/504 或入口 20s 未挂载时重试一次；若后续回归仍偶发，建议提单给测试服运维（不为它加更多重试掩盖）。
2. [page_map 主入口 selector 已对齐] 24 页 page_map 的 `states.landing.buttons.main_upload.selector` 由 `input[type=file]` 更正为实测主入口：22 页 `button.seo-first-screen-upload-button`（+`fallback_selector: input[type=file]`），L2-001 / L2-010 保持 `input[type=file]`（实测无该按钮）。data 同步补 `upload_selector` / `upload_fallback_selector`，脚本不再靠文案硬猜。此为 page-map-sync 职责范围内的就近纠偏，建议后续由 page-map-sync 复核一次。
3. [面板断言口径] 断言已是「激活 tab == page_map 默认面板」的强断言（R6），且等工具预设生效后再读；后续维护不要回退为「激活 tab ∈ tab 集合」。
4. [归档清理] 本轮新增根目录一次性脚本（`probe_panel_timing*.py`、`probe_layer_selected*.py`、`probe_landing_selectors.py`、`probe_r8_landing.py`、`_patch_*.py`、`_fix_pagemap_notes.py`、`_write_review.py`、`mcp_client.py` 等），归档阶段按 archive-cleanup 生成 manifest 后备份到 `evidence/oneoff_scripts/` 再删除。

# Checked Items

- [x] **断言完整性**：路由类型 / 处理态结束 / 底部主面板可见（legacy_canvas）/ **默认激活面板等值** / tab 数 ≥3 / **图层默认选中（选中框 + ≥4 手柄）** / 画布已渲染 / special 用例关键词。无 `assert True`、无 `skip`、无 `xfail`。
- [x] **未弱化断言**：R6 由集合断言加强为等值断言；R7 新增图层选中断言；R8 只动「入口定位与重试」，未改任何 expected。
- [x] **selector 合规**：执行路径仅用 `.mobile-primary-panel`、`.mobile-primary-panel__tab-text--active`、`button.seo-first-screen-upload-button`、`.choose-boder`、`.choose-boder .scale-point`、`input[type=file]`；无通配、无 `:nth-child`、无位置 XPath、无 hash class。
- [x] **等待正确性**：`_open_target` 等入口挂载（≤20s，网关错误重试 1 次）→ `_start_upload` 主 selector 点击 + `expect_file_chooser`（15s）→ 等处理态结束 → 等默认面板激活（≤15s）→ 等画布渲染 → 等选中框与手柄同现（≤15s）。全部有界，均非单纯 sleep。
- [x] **架构**：测试在 `tests/mobile/`；移动端 fixture 独立、会话级只登录一次；全中文注释与 Allure step。
- [x] **数据外置**：24 条参数（page_path / route / default_panel / expected_canvas / required_keywords / timeout_ms / screenshot / **upload_selector** / upload_fallback_selector）全部在 `data/pokecut_seo_main_upload_mobile_interactions_v1.yaml`。
- [x] **引用一致性**：24 份 page_map 存在且 YAML 可解析；`state_ref=states.landing.buttons.main_upload`；用例数 24 == `cases.md` `case_count` == collect-only 24。
- [x] **上传素材合规**：统一 `test_images/1K.jpg`，真实按钮 + `expect_file_chooser()` 为主，无生成/下载/换图。
- [x] **报告层级与截图**：`feature/story/title/case_id/layer/severity` 齐备，无 `parentSuite`；每条用例稳定态整页截图 + `allure.attach.file`，24/24 覆盖。
- [x] **自跑证据**：R8 全量 **24 passed ×2**（227.42s / 223.65s）；R7 定向 7 passed；R6 全量 24 passed ×2；R5 全量 24 passed。
