---
task_id: new_feature_detection_ui_20260901_124711
agent: ui-test-page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: null
inputs:
  requirement_doc: "D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md"
  target_urls:
    - "https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector"
    - "https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader"
  driver: playwright_mcp_only
  account_used: "会员账号 450832596@qq.com；免费新账号曾用于验证 credits 不足购买弹窗"
  upload_asset: "D:/Test/web-test/test_images/有人脸.JPG"
outputs:
  scanned_pages:
    - nose-shape-detector
    - ai-face-reader
  page_map_versions:
    - "page_map/pokecut/nose_shape_detector_v2.yaml"
    - "page_map/pokecut/ai_face_reader_v2.yaml"
  coverage_gates:
    mcp_connectivity: passed
    seo_default_pc: covered
    logged_in_upload_pc: covered
    analysis_failure_server_busy: covered
    nose_blur_placeholder_pc: covered_with_bug_candidate
    nose_get_it_now_to_canvas_pc: covered
    nose_mobile_vertical_error_blur: covered_with_bug_candidate
    face_success_three_columns: blocked_by_dependency
    download_jpg: blocked_by_dependency
    continue_portrait_success_pc_mobile: blocked_by_dependency
  state_button_coverage:
    covered: 17
    blocked_by_dependency: 4
    skipped: 5
  requirement_actual_diffs:
    - id: REQ-SEO-DEFAULT
      diff_type: covered
      expected: 上传前保持原 SEO 内容结构和文案，不出现三栏承接 UI。
      actual: 两个页面 PC 默认态均保持 SEO H1/描述/上传框/SEO 内容，未出现 Original/Analysis/Optimized 三栏。
      evidence: [mcp_nose_default_snapshot_deep.md, mcp_face_default_snapshot.md]
    - id: REQ-NOSE-BLUR
      diff_type: covered
      expected: nose 页结果态无真实优化图；Optimized Result 显示原图缩略图、模糊蒙层、固定文案、Get It Now；不显示下载按钮。
      actual: PC 与移动端均观察到 Optimized Result 承接位、固定文案和 Get It Now；区域内无 Download；点击 PC Get It Now 进入 /agent?pid=...，原图图层被选中并打开 Portrait Editor/Face 面板。
      evidence: [mcp_nose_result_server_busy_blur.png, mcp_nose_getitnow_canvas.png, mcp_nose_mobile_result_snapshot.md]
    - id: REQ-NOSE-ANALYSIS-FAIL-WAITING
      diff_type: bug_candidate
      expected: 分析结果未成功显示前，优化结果区始终保持 Waiting for analysis...，页面不跳转无限画布页。
      actual: nose 页 Analysis Result 已显示 Server busy 失败，但 Optimized Result 同时显示模糊承接位 + Get It Now；点击后可跳转无限画布页。
      impact: 用户在分析失败时仍可进入后续 Portrait Editor 承接，和“优化等待态直到分析成功”的需求冲突。
      recommended_action: file_bug
      evidence: [mcp_nose_generating_snapshot.md, mcp_nose_getitnow_canvas.png]
    - id: REQ-FACE-SERVER-BUSY
      diff_type: covered
      expected: 分析服务器失败显示 Server busy. We're fixing it now. No credits deducted.，出现 Change Image / Try again，优化区保持等待态。
      actual: ai-face-reader 上传本地图片和点击示例图均进入三栏后显示该 Server busy 文案；Change Image / Try again 可见；Analysis Download disabled；Optimized Result 显示 Waiting for analysis...，Download 和 Continue disabled；Try again 后仍保持同失败态。
      evidence: [mcp_face_after_upload_snapshot.md, mcp_face_sample_after_wait_snapshot.md, mcp_face_retry_snapshot.md]
    - id: REQ-FACE-SUCCESS-THREE-COLUMNS
      diff_type: skipped
      reason: 测试服后端生成持续返回 Server busy，无法获得成功的分析图/优化图；纯 Playwright MCP 不做接口 mock 或故障注入。
      expected: 成功态展示三栏，Analysis/Optimized 两个 Download 可下载 jpg，Continue in Portrait Editor 可携带三张图进入画布。
      actual: 仅覆盖到三栏容器与失败/等待态，未覆盖成功图、jpg 下载、成功态 Continue。
      diagnostic_limit: playwright_mcp_only_no_devtools_trace
  bug_candidates:
    - id: BUG-NOSE-001
      severity: high
      title: nose-shape-detector 分析失败时 Optimized Result 错误显示 Get It Now 并允许进入画布
      page: https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
      steps:
        - 登录会员账号 450832596@qq.com。
        - 上传 D:/Test/web-test/test_images/有人脸.JPG。
        - 观察 Analysis Result 与 Optimized Result。
        - 点击 Get It Now。
      expected: 分析结果未成功前，优化区保持 Waiting for analysis...，Download/Continue/Get It Now 不应可用；不应跳转画布。
      actual: Analysis Result 显示 Server busy，但 Optimized Result 显示模糊承接文案和 Get It Now；点击跳转 /agent?pid=... 并打开 Portrait Editor 面板。
      evidence:
        - artifacts/new_feature_detection_ui_20260901_124711/shots/mcp_nose_generating_snapshot.md
        - artifacts/new_feature_detection_ui_20260901_124711/shots/mcp_nose_result_server_busy_blur.png
        - artifacts/new_feature_detection_ui_20260901_124711/shots/mcp_nose_getitnow_canvas.png
  skipped:
    - id: SKIP-FACE-SUCCESS
      reason: 后端生成依赖不可用，ai-face-reader 分析持续 Server busy。
    - id: SKIP-DOWNLOAD-JPG
      reason: 未进入成功态，Download 均 disabled，无法验证 jpg 下载。
    - id: SKIP-CONTINUE-SUCCESS-PC
      reason: 未进入成功态，Continue in Portrait Editor disabled。
    - id: SKIP-MOBILE-FACE-SUCCESS
      reason: PC 成功态已被后端阻塞，移动端成功态未重复消耗探索。
    - id: SKIP-FAILURE-INJECTION
      reason: 纯 Playwright MCP 不做网络错误/鉴黄/优化失败/credits 扣返等故障注入。
  special_dependencies:
    - 后端生成服务需恢复才能覆盖成功态与下载态。
    - credits 不足购买成功流程涉及真实支付/订阅，未授权不执行。
  specs_updated: []
next_agent: null
created_at: "2026-09-01 14:28:00"
---

# 探索摘要

本轮已按用户要求先验证 MCP：`browser_navigate` 打开 `https://pokecut-dev.guangzhuiyuan.com/` 成功，确认 Playwright MCP 可用。随后全程使用 Playwright MCP 的 navigate / snapshot / click / file_upload / resize / screenshot 完成两个目标页探索，未使用脚本或 DevTools 诊断。

- `nose-shape-detector`：默认 SEO 态 covered；上传后出现三栏，但分析区测试服返回 Server busy；优化区却出现无优化图承接态和 `Get It Now`，点击可进入无限画布 Portrait Editor，构成 bug_candidate。
- `ai-face-reader`：默认 SEO 态 covered；上传本地图片、点击示例图均进入三栏但分析区返回 Server busy；优化区保持 `Waiting for analysis...`，Download/Continue disabled，符合服务器忙失败预期；成功三栏、下载 jpg、成功态 Continue 因后端阻塞未覆盖。
- 移动端：已在 390x844 对 nose 页复测上传后纵向三块区域，复现同一 nose bug；ai-face-reader 移动成功态因 PC 生成已阻塞未重复探索。

# 页面覆盖矩阵

| 页面 | PC 默认 SEO | PC 上传/结果 | Get It Now/Continue | 移动端 | 结论 |
|---|---:|---:|---:|---:|---|
| nose-shape-detector | ✅ | ⚠️ 分析失败但模糊承接出现 | ✅ Get It Now 入画布 | ⚠️ 纵向 + 同 bug | 有阻塞级候选缺陷 |
| ai-face-reader | ✅ | ⚠️ 服务器忙失败态 | ⚠️ Continue disabled，成功态未达 | ⏸️ 未重复 | 后端阻塞成功态覆盖 |

# 需求差异与关键发现

1. 上传前 SEO 默认态符合：两个页面未上传时都未出现结果编辑三栏。
2. nose 无优化结果图承接 UI 形态本身符合：显示 `Optimized Result`、模糊缩略图承接文案、`Get It Now`，且无真实优化下载按钮。
3. **BUG-NOSE-001**：nose 在分析图 Server busy 失败时仍显示 `Get It Now` 并允许进画布；这违背“分析结果未成功显示前，优化结果区始终保持等待态”的用例。
4. ai-face-reader 服务器忙失败态符合需求：显示准确文案、`Change Image` / `Try again`，优化区等待，相关按钮 disabled。
5. ai-face-reader 成功态未覆盖：后端持续 `Server busy`，无法确认三栏成功图、两个 jpg 下载和成功态 Continue 携带三图逻辑。

# 状态化按钮覆盖摘要

- 已覆盖：上传主按钮、登录表单、Upload Image disabled、Change Image、Try again、Analysis Download disabled、Optimized Download disabled、Continue disabled、nose Get It Now、购买/积分弹窗关闭/拒绝入口。
- 阻塞：成功态 Upload Image 恢复可用、Analysis Download jpg、Optimized Download jpg、成功态 Continue in Portrait Editor。
- 未授权/不可注入：真实购买成功、网络错误、鉴黄失败、优化失败返还 credits。

# 版本差异摘要

- 新增 `page_map/pokecut/nose_shape_detector_v2.yaml`：补充纯 MCP 证据下的登录后上传、Server busy + blur 承接、Get It Now 画布承接、移动端纵向复现状态。
- 新增 `page_map/pokecut/ai_face_reader_v2.yaml`：补充纯 MCP 证据下的默认态、示例图/本地图上传、Server busy 失败态、成功态 blocked_by_dependency 按钮定义。

# Gate

`sync` 当前为 `pending_review`。请审核以上覆盖矩阵、BUG-NOSE-001 以及 blocked/skipped 项；确认后才能进入后续用例设计/脚本编写阶段。
