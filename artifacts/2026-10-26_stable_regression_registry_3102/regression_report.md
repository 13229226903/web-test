# Regression Registry 3102 Final Regression Report

- Task: `2026-10-26_stable_regression_registry_3102`
- Target URL: `http://10.17.1.66:3102/`
- Scope: stable_regression scripts in `artifacts/regression_registry.md`
- Final Allure: `D:\Test\web-test\artifacts\2026-10-26_stable_regression_registry_3102\allure-report-final-20261026-190014/index.html`

## Conclusion

After backend recovery, remaining registry stable_regression scripts were all rerun. Final result is not fully green: 24 failed/XPASS cases remain, mainly in cost rules, analytics events, generation network errors, legacy canvas AI tools, and portrait detector waits.

`tests/test_infinite_canvas_enhance_v4.py` is `pending_fix`, not included as stable regression.

## Resume Results

| Script | Result |
|---|---|
| tests/test_ai_image_text_enhancer_experiment.py | 13 passed / 3 failed / 2 skipped |
| tests/test_detection_ui_seo_l6.py | 2 passed |
| tests/test_pokecut_pc_batch_v1.py | 13 passed / 3 failed |
| tests/test_old_canvas_insert_panel_v3.py | 24 passed |
| tests/test_old_canvas_text_panel_v1.py | 13 passed |
| tests/test_old_canvas_sticker_panel_v1.py | 9 passed |
| tests/test_seo_main_upload_interactions_v1.py | 24 passed |
| tests/mobile/test_seo_main_upload_mobile_v1.py | 23 passed / 1 xfailed |
| tests/test_create_chat_to_edit_auto_v1.py | 11 passed |
| tests/test_canvas_stats_all.py | 29 passed / 7 failed / 2 skipped / 2 xfailed |
| tests/test_old_canvas_ai_tools_all.py | 4 passed / 2 failed |
| tests/test_infinite_canvas_sticker_v1.py | 5 passed |
| tests/test_infinite_canvas_text_layer_v2.py | 6 passed |
| tests/test_pokecut_portrait_detector.py | 5 passed / 9 failed |

## Main Failures

- AI Image Text Enhancer: expected cost 25 but actual 10; free trial expected free but actual paid.
- PC Batch: Change BG was not auto-selected; Enhance pages showed Network error.
- Canvas Stats: mobile registration/modal analytics events missing; PC new canvas did not trigger Yearly Ultra Debug skip-purchase; 2 known-bug XPASS.
- Old Canvas AI Tools: preset-select group and mode+category group failed.
- Portrait Detector: 6 result waits timed out; 3 exception/auth UI states missing.

## Artifacts

- Regression report: `artifacts/2026-10-26_stable_regression_registry_3102/regression_report.md`
- Final Allure: `D:\Test\web-test\artifacts\2026-10-26_stable_regression_registry_3102\allure-report-final-20261026-190014/index.html`
- Resume logs: `artifacts/2026-10-26_stable_regression_registry_3102/logs-resume/`

## Bug Report

- artifacts/2026-10-26_stable_regression_registry_3102/evidence/bug_report_regression_20261026.md
