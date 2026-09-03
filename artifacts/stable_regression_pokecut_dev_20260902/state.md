task_id: stable_regression_pokecut_dev_20260902
task_type: stable_regression
status: done
execution_mode: codex_single_context
base_url: https://pokecut-dev.guangzhuiyuan.com/
result:
  total: 89
  passed: 85
  failed: 1
  skipped: 3
  duration_s: 2191.25
per_file:
  test_pokecut_portrait_detector.py: 14 passed
  test_ai_image_text_enhancer_experiment.py: 16 passed, 2 skipped
  test_infinite_canvas_text_layer_v2.py: 6 passed
  test_mobile_home.py: 36 passed, 1 failed, 1 skipped
  test_help_page.py: 11 passed
  test_detection_ui_seo_l6.py: 2 passed
failed:
  - file: tests/test_mobile_home.py::TestL2Interactions::test_l2_010_effect_template
    reason: Locator.click Timeout 15000ms 等待 button name='Butt'（effect 模板卡）未出现
report:
  allure_results: reports/allure-results-regression-clean
  allure_report: reports/allure-report-regression
  url: http://localhost:8123/index.html
created_at: 2026-09-02 15:03:08
updated_at: 2026-09-02 15:53:41
