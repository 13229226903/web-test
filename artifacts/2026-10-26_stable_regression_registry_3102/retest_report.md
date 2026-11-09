# 失败用例复测报告 — 2026-10-26

- 环境：`http://10.17.1.66:3102`
- 范围：上一次 regression_registry 失败用例，共 5 组 24 条
- Allure：`D:\Test\web-test\artifacts\2026-10-26_stable_regression_registry_3102\allure-report-retest-20261026-204828/index.html`
- 日志目录：`artifacts/2026-10-26_stable_regression_registry_3102/logs-retest/`

## 复测结论

| 组 | 结果 | 恢复 | 仍失败 |
|---|---|---|---|
| AI Image Text Enhancer | 0 passed / 3 failed | 无 | 3 |
| PC Batch | 1 passed / 2 failed | test_l2_006_changebg_colors | 2 |
| Canvas Stats | 1 passed / 6 failed | test_m_core_02 | 6 |
| Old Canvas AI Tools | 0 passed / 2 failed | 无 | 2 |
| Portrait Detector | 1 passed / 8 failed | test_l3_001_anonymous_auth | 8 |

## 仍失败用例

### AI Image Text Enhancer
- test_text_l4_cost_refresh_and_rules：Enhance 显示 10，期望 25
- test_text_l4_free_trial_display_free：免费试用态显示 paid，期望 free
- test_text_l4_single_purchase_cost_rules：Enhance 显示 10，期望 25

### PC Batch
- test_l2_008_enhance_modes_submit：Enhance 面板出现 Network error
- test_l6_002_smoke_enhance_resize_download：Enhance 面板出现 Network error

### Canvas Stats
- test_p_new_10 / test_p_new_11：PC 新画布未触发 Yearly Ultra Debug 跳过购买
- test_p_new_16 / test_m_new_14：BUG-2026-1012-01 XPASS(strict) 仍出现
- test_m_core_01：移动端核心注册 sendGaEvent 期望 1 实际 0
- test_m_core_05：移动端 AI 弹层 sendGaEvent 期望 1 实际 0

### Old Canvas AI Tools
- test_p_ait_01_preset_select_group：Photo Enhancer 120s 内 Confirm/Cancel 未同时可用
- test_p_ait_02_mode_and_category_group：AI Clothes Changer Formal Wear 180s 内未结束

### Portrait Detector
- 6 条结果态等待超时：Ethnicity / Body / Face / questionnaire / unsaved report / Try My Photo
- test_l3_004_noface：No Face Found 未出现
- test_l3_005_multiface：Choose a Face to Analyze 未出现

## 本次恢复通过
- tests/test_pokecut_pc_batch_v1.py::TestL2BatchInteractions::test_l2_006_changebg_colors
- tests/test_canvas_stats_all.py::test_m_core_02
- tests/test_pokecut_portrait_detector.py::TestL3Exception::test_l3_001_anonymous_auth
