# Regression Registry @ http://10.17.1.66:3001 回归报告

- 任务：`2026-10-27_regression_registry_3001`
- 目标：`http://10.17.1.66:3001/`
- 范围：`artifacts/regression_registry.md` 中 17 条 stable_regression 脚本
- 排除：`tests/test_infinite_canvas_enhance_v4.py`（registry status=pending_fix）
- Allure：`D:\Test\web-test\artifacts\2026-10-27_regression_registry_3001\allure-report-20261027-190041/index.html`

## 总体结果

共执行 17 个稳定回归脚本，累计：

- passed：235
- failed：25
- skipped：5
- xfailed：3

整体不是全绿，失败集中在 Portrait Detector、AI Image Text Enhancer、Mobile Home、SEO 上传、Canvas Stats、Old Canvas AI Tools。

## 脚本结果

| # | 脚本 | 结果 |
|---:|---|---|
| 1 | tests/test_pokecut_portrait_detector.py | 9 failed / 5 passed |
| 2 | tests/test_ai_image_text_enhancer_experiment.py | 4 failed / 11 passed / 3 skipped |
| 3 | tests/test_infinite_canvas_text_layer_v2.py | 6 passed |
| 4 | tests/test_mobile_home.py | 2 failed / 36 passed |
| 5 | tests/test_help_page.py | 11 passed |
| 6 | tests/test_detection_ui_seo_l6.py | 2 passed |
| 7 | tests/test_pokecut_pc_home_v6.py | 17 passed |
| 8 | tests/test_pokecut_pc_batch_v1.py | 16 passed |
| 9 | tests/test_old_canvas_insert_panel_v3.py | 24 passed |
| 10 | tests/test_old_canvas_text_panel_v1.py | 13 passed |
| 11 | tests/test_old_canvas_sticker_panel_v1.py | 9 passed |
| 12 | tests/test_seo_main_upload_interactions_v1.py | 1 failed / 23 passed |
| 13 | tests/mobile/test_seo_main_upload_mobile_v1.py | 1 failed / 22 passed / 1 xfailed |
| 14 | tests/test_create_chat_to_edit_auto_v1.py | 11 passed |
| 15 | tests/test_canvas_stats_all.py | 7 failed / 29 passed / 2 skipped / 2 xfailed |
| 16 | tests/test_old_canvas_ai_tools_all.py | 1 failed / 5 passed |
| 17 | tests/test_infinite_canvas_sticker_v1.py | 5 passed |

## 失败明细

### Portrait Detector（9）

- Ethn / Body / Face / questionnaire / unsaved report / Try My Photo：结果态等待 `Download report` 超时
- `test_l3_001_anonymous_auth`：匿名上传后未出现 `[data-testid="auth-dialog"]`
- `test_l3_004_noface`：未出现 `No Face Found`
- `test_l3_005_multiface`：未出现 `Choose a Face to Analyze`

### AI Image Text Enhancer（4）

- `test_text_l2_resolution_visibility_and_disabled`：remove_glare 期望 5，实际 10
- `test_text_l4_cost_refresh_and_rules`：8k + 全选期望 25，实际 30
- `test_text_l4_member_free_icon_and_cost`：会员 8k + 全选期望 25，实际 30
- `test_text_l4_single_purchase_cost_rules`：单项购买 8k + 全选期望 25，实际 30

### Mobile Home（2）

- `test_l2_008_id_photo_anonymous`：匿名 ID Photo 上传后未出现 `Get Free Credits` / `Get Up to`
- `test_l3_004_id_photo_success`：登录态 ID Photo 上传后 URL 仍在首页，未进入 `/tools/id-photo-edit?pid=`

### SEO Main Upload（PC 1 / Mobile 1）

- PC `test_l2_005`、Mobile `test_l2_005`：`/tools/cv-photo-editor` 上传后 URL 仍停在 `/tools/cv-photo-editor`，未进入 `/tools/id-photo-edit?pid=`

### Canvas Stats（7）

- `test_p_new_10` / `test_p_new_11`：PC 新画布未完成 Yearly Ultra Debug 跳过购买
- `test_p_new_16` / `test_m_new_14`：已知 bug `BUG-2026-1012-01` XPASS(strict)
- `test_m_core_01`：移动端核心注册埋点 `sendGaEvent` 期望 1，实际 0
- `test_m_core_02`：enhance 未出现注册弹窗
- `test_m_core_05`：移动端 AI 消除弹窗出现埋点期望 1，实际 0

### Old Canvas AI Tools（1）

- `test_p_ait_02_mode_and_category_group`：AI Clothes Changer Formal Wear 在 180s 内未进入结束态，`Confirm/Cancel` 未同时可用

## 结论

- `3001` 与 `3102` 的共同失败：Portrait Detector、Canvas Stats、Old Canvas AI Tools AI Clothes Changer、SEO 上传 cv-photo-editor。
- `3001` 独有的点数规则/ID Photo 失败，可能是环境差异或后端版本差异，建议优先确认。
- PC Batch 的 Network error 在 `3001` 未复现，说明更偏环境稳定性问题。
- 已通过：Infinite Canvas Text、Help、Detection UI、PC Home、PC Batch、Old Canvas Insert/Text/Sticker、Create Chat to Edit Auto、Infinite Canvas Sticker。
