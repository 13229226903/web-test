---
task_id: new_feature_detection_ui_20260901_124711
agent: review
status: completed
inputs:
  impl: artifacts/new_feature_detection_ui_20260901_124711/impl.md
  test_file: tests/test_detection_ui_seo_l6.py
  data_file: data/pokecut_detection_ui.yaml
  cases: artifacts/new_feature_detection_ui_20260901_124711/cases.md
  page_maps:
    - page_map/pokecut/nose_shape_detector_v3.yaml
    - page_map/pokecut/ai_face_reader_v3.yaml
  note: 工作区非 git 仓库，无法用 git diff；以文件清单与内容比对代替 files_changed 校验
outputs:
  verdict: pass
  blocking_issue_count: 0
  suggestion_count: 3
  next_agent: test-writing(report-output)
created_at: 2026-09-02 12:55:00 +08:00
---

# review.md — 检测类功能适配 UI L6 冒烟实现静态审查

## Blocking Issues
无。

## Suggestions
1. 代码未实际读取 `data/pokecut_detection_ui.yaml`，选择器与常量在代码内硬编码；当前与 yaml 内容一致，建议后续接入数据驱动读取，避免双维护漂移。
2. 两个 Download 按钮通过 `get_by_role("button", name="Download").nth(0/1)` 区分分析图/优化图，属位置索引；与 page_map 中 `>> nth=0/1` 文档一致且已自跑通过，暂不阻塞，建议后续若 DOM 顺序变化改为按列容器作用域定位。
3. `.debug-panel` / `.purchase-gift-modal` 等 class 定位非 hash class，且有 page_map/conftest 背书；如后续重构建议沉淀为页面专属稳定属性。

## Checked Items
- 断言完整性：两条用例均有有意义断言（三栏标题、下载文件名前缀与 .jpg、画布 URL/图层/Panel/Generate disabled），未删除/弱化断言，expected 无空/0/-。
- 期望合理性：文本断言使用子串包含，避免过精确格式漂移。
- selector 红线：无通配 `*`、无 `:nth-child`、无位置 XPath、无 hash class；`data-testid` / `has-text` / alt / role 稳定定位；`.nth()` 位置用法已在 page_map 中背书（见 Suggestions 2）。
- 架构与注释：测试位于 `tests/test_detection_ui_seo_l6.py`，数据外置 `data/pokecut_detection_ui.yaml`，中文注释；沿用仓库既有 Vue 坐标点击 + file chooser + dispatchEvent 约定。
- 引用一致性：impl.md 列出的 test_file/data_file 与磁盘一致；cases.md 的 page_ref 均能在 v3 page_map 中解析（predeploy_success_three_columns_desktop / predeploy_analysis_success_blur_desktop 及其 buttons）；按钮交互均从 page_map 文档化按钮语义执行。
- Allure 层级：epic=检测类功能适配UI、feature=L6 核心 Happy Path / E2E、story=L6-检测类SEO页全流程、title=L6-001/L6-002，与 cases.md 一致；两条用例 docstring 均含 PRD引用/覆盖层级/前置条件/测试步骤/预期结果。
- 截图覆盖：L6-001 含 face_e2e_success.png、face_e2e_canvas.png；L6-002 含 nose_e2e_blur.png、nose_e2e_canvas.png；fixture teardown 另附“用例截图”，满足每条矩阵用例 ≥1 截图要求。
- 自跑证据：impl.md 记录 collect-only 2 collected、self_run 2 passed in 131.41s。
