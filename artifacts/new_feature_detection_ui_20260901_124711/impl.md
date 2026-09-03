---
task_id: new_feature_detection_ui_20260901_124711
agent: test-writing
status: completed
inputs:
  cases: artifacts/new_feature_detection_ui_20260901_124711/cases.md (confirmed, 仅 L6 两条 smoke)
  page_maps:
    - page_map/pokecut/nose_shape_detector_v3.yaml
    - page_map/pokecut/ai_face_reader_v3.yaml
  environment: https://pokecut-dev.guangzhuiyuan.com（预部署登录会员账号 450832596@qq.com）
outputs:
  test_file: tests/test_detection_ui_seo_l6.py
  data_file: data/pokecut_detection_ui.yaml
  collect_only: "2 tests collected, 0 error/warning；ID 与 cases.md L6-001/L6-002 一致"
  self_run: "2 passed in 131.41s（face L6-001 与 nose L6-002 均通过）"
  allure_results: reports/allure-results
regression_candidate:
  eligible: true
  reason: 预部署环境成功态 E2E 两条已跑通，可作为后续 stable_regression 基线；依赖预部署环境与会员账号
  suggested_tests: [tests/test_detection_ui_seo_l6.py::test_l6_001_face_full_flow, tests/test_detection_ui_seo_l6.py::test_l6_002_nose_full_flow]
  suggested_archive: 检测类功能适配UI（face 三栏/nose 模糊承接）L6 E2E
  registry_key: TBD（待归档 gate 登记）
next_agent: review
created_at: 2026-09-02 12:50:00 +08:00
updated_at: 2026-09-02 12:50:00 +08:00
---

# impl.md — 检测类功能适配 UI L6 冒烟实现

## 实现摘要
- 依据 confirmed cases.md（仅保留 L6-001 / L6-002）编写 `tests/test_detection_ui_seo_l6.py` 与数据文件 `data/pokecut_detection_ui.yaml`。
- 测试以会话级 `predeploy_context` fixture 复用登录态：先通过 DEBUG 面板切「预部署」并登录会员账号，再开新页执行用例；上传统一走真实按钮 + `expect_file_chooser`。
- Vue 交互使用坐标点击；下载用 `expect_download` 断言 `pokecut-analysis-result-*.jpg` / `pokecut-optimized-result-*.jpg`；画布承接断言 `/agent?pid=`、图层 img、Portrait Editor/Face 面板、Generate disabled。
- 环境：`--base-url=https://pokecut-dev.guangzhuiyuan.com`（覆盖 pytest.ini 默认内网 base_url，符合用户指定测试服域名）。

## 实现要点
- L6-001 face：上传 有人脸.JPG → 等 Analysis Result Download 可用 → 等 Optimized Result img+Download 可用 → 下载分析图/优化图并校验文件名 → Continue in Portrait Editor → 画布断言三图 + Portrait Editor/Face 面板 + Generate disabled。
- L6-002 nose：上传 有人脸.JPG → 等 Analysis Result Download 可用 → 校验 Optimized Result 模糊承接文案与 Get It Now，且全页仅 1 个 Download（无优化图下载按钮）→ 点击 Get It Now → 画布断言仅原图 + Portrait Editor/Face 面板 + Generate disabled。
- 自修日志：
  - round 1 失败：上传按钮用 `get_by_role("button", name="Try Image to Image AI Now")` 找不到元素（该文本在 dropzone 内层，外层 button 的 accessible name 是 “or drop a file here...”）；改为 `get_by_text("Try Image to Image AI Now")`。
  - round 1 同时修正等待函数：`h3.closest('div')` 只回到标题头块，未包含 Download/图片；改为沿祖先向上最多 8 层找包含 Download 的列容器。
  - round 1 补充 goto 后 `close_modal_if_present`，避免登录态限时购买浮层遮挡上传区。
  - round 2：2 条用例全部通过。

## 命令与结果
- collect-only：`python -m pytest tests/test_detection_ui_seo_l6.py --collect-only -q --base-url=https://pokecut-dev.guangzhuiyuan.com` → 2 tests collected, 0 error/warning。
- 自跑：`python -m pytest tests/test_detection_ui_seo_l6.py -v --base-url=https://pokecut-dev.guangzhuiyuan.com --alluredir=reports/allure-results --tb=long`
  - 结果：`2 passed in 131.41s`。
- 失败归因：无（2 条通过）。

## 报告与截图说明
- Allure 结果已写入 `reports/allure-results`；report-output（allure-report-matrix + 简易报告）按 orchestrator 规则在 review 通过后生成。
- 用例内按 cases.md 截图点 attach：`face_e2e_success.png`、`face_e2e_canvas.png`、`nose_e2e_blur.png`、`nose_e2e_canvas.png`，每个关键断言步骤均有截图。
