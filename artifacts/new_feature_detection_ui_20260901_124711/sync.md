---
task_id: new_feature_detection_ui_20260901_124711
agent: page-map-sync
status: confirmed
repair_scope: full_exploration
gate_exemption: false
inputs:
  - D:\downloads\用例\task-39-飞书文档_ 检测类功能适配UI需求文档 (1)\检测类功能适配UI需求文档.md
  - https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
  - https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader
  - driver: playwright_mcp_only
outputs:
  scanned_pages: [/tools/nose-shape-detector, /tools/ai-face-reader, /agent?pid=<uuid>]
  page_map_versions: [nose_shape_detector_v3.yaml, ai_face_reader_v3.yaml]
  coverage_gates: {mcp_connectivity: covered, test_backend_initial: covered, predeploy_generation_success: covered, desktop_success_downloads: covered, desktop_reupload_generating: covered, desktop_continue_canvas: covered, nose_get_it_now_canvas: covered, mobile_success_layout: covered, mobile_continue_canvas: gap}
  state_button_coverage: "covered: Upload Image enabled/disabled, Analysis Download, Optimized Download, Continue in Portrait Editor, Get It Now, Try again/Change Image；skipped: payment success and forced failure injection"
  requirement_actual_diffs:
    - {case: "nose 分析失败前优化区等待态", diff_type: bug_candidate, detail: "测试服 Analysis Server busy 时 Optimized Result 仍显示 Get It Now 并可跳转画布；预部署分析成功后 Get It Now 承接正常"}
    - {case: "ai-face-reader 移动端 Continue 仅携带优化结果图", diff_type: bug_candidate, detail: "390x844 下成功态点击 Continue 后，画布实际带入 图片 1/2/3 三张图，而非仅优化结果图"}
    - {id: BUG-NOSE-001, severity: high, page: /tools/nose-shape-detector, detail: "测试服分析失败时 Optimized Result 错误展示 Get It Now 并允许进入画布"}
    - {id: BUG-FACE-MOBILE-001, severity: high, page: /tools/ai-face-reader, detail: "移动端成功态 Continue in Portrait Editor 实际携带三张图，和需求仅携带优化结果图不一致"}
  skipped:
    - {item: "真实购买成功后恢复生成", reason: "涉及真实支付/订阅，未授权不执行；仅观察到非生产 debug 存在跳过真实购买开关，未使用"}
    - {item: "网络错误/鉴黄/优化失败/credits 扣返故障注入", reason: "本次限定 Playwright MCP 页面探索，不做接口 mock/DevTools 诊断/故障注入"}
  special_dependencies: ["测试服生成持续 Server busy 时，按 PROJECT.md 切预部署并重新登录后补测成功态", "生成态成功证据来自预部署环境", "下载文件已复制到 shots/downloads"]
  specs_updated: false
next_agent: test-case-design
created_at: 2026-09-01 20:00:00 +08:00
confirmed_at: 2026-09-02 12:05:44
reviewer_decision: 用户确认 BUG-NOSE-001 与 BUG-FACE-MOBILE-001 先 skip，允许进入 test-case-design
---

# sync.md — 检测类功能适配 UI 纯 MCP 探索

## 1. 探索摘要
- 已按 page-map-sync 规则补充“生成态后的交互”：测试服仍先试，`ai-face-reader` / `nose-shape-detector` 在测试服曾出现 Server busy；随后通过页面 `DEBUG` 面板切到 `预部署`，刷新后重新登录会员账号 `450832596@qq.com` 再上传素材继续探索。
- `ai-face-reader` 预部署成功进入三栏结果态：PC 从左到右依次展示 `Original Image`、`Analysis Result`、`Optimized Result`；原图区 `Upload Image` 可用；分析区与优化区均展示真实结果图和 `Download`；优化区 `Continue in Portrait Editor` 可用。
- `ai-face-reader` 成功态后交互已覆盖：分析图 Download 下载 `pokecut-analysis-result-*.jpg`；优化图 Download 下载 `pokecut-optimized-result-*.jpg`；点击 `Upload Image` 重新选择 `test_images/多人脸.jpg` 后重新进入 `Generating analysis...` / `Waiting for analysis...`，按钮恢复 disabled；再次成功后 PC Continue 进入画布并带入三张图，优化图选中，Portrait Editor/Face 面板打开。
- `nose-shape-detector` 预部署分析成功后展示无优化图承接态：Original / Analysis / Optimized 三块存在，Analysis 有真实结果图和 Download；Optimized 只展示模糊承接文案与 `Get It Now`，无 Download；点击 `Get It Now` 进入画布，仅带入原图，原图选中，Portrait Editor/Face 面板打开。
- 移动端 390x844 成功态已补测 `ai-face-reader`：页面纵向展示 Original / Analysis / Optimized，按钮文案与 PC 一致；但点击移动端 `Continue in Portrait Editor` 后，画布实际带入 图片 1/2/3 三张图，和需求“仅带优化结果图”冲突，新增 BUG-FACE-MOBILE-001。
- 本轮补充仍全程使用 Playwright MCP 的页面交互和截图 / snapshot；下载事件由 MCP 返回并已把 jpg 文件复制到 `shots/downloads/` 作为证据。

## 2. 页面覆盖矩阵（对照需求 16 条 AC）
| # | 用例/覆盖点 | 结论 | 证据 |
|---|---|---|---|
| 1 | 上传前保持原 SEO 内容结构和文案 | covered | `shots/mcp_nose_default_snapshot_deep.md`；`shots/mcp_face_default_snapshot.md` |
| 2 | 有优化结果图页面成功态展示三栏结果态 | covered | `shots/mcp_face_predeploy_success_snapshot.md`；`shots/mcp_face_predeploy_success_before_continue.png` |
| 3 | 无优化结果图页面展示模糊承接态 | covered | `shots/mcp_nose_predeploy_success_blur_snapshot.md`；Optimized 区无 Download，仅 `Get It Now` |
| 4 | nose 点击 `Get It Now` 进入 Portrait Editor 承接 | covered | `shots/mcp_nose_predeploy_getitnow_canvas_snapshot.md`；`shots/mcp_nose_predeploy_getitnow_canvas.png` |
| 5 | 结果生成中原图展示缩略图且 Upload Image 不可点击 | covered | `shots/mcp_face_reupload_generating_snapshot.md`；Analysis `Generating analysis...` 时 Upload Image disabled |
| 6 | 分析生成中灰色蒙层/`Generating analysis...` | covered | `shots/mcp_face_reupload_generating_snapshot.md` |
| 7 | 分析未成功前优化区保持 `Waiting for analysis...` | gap / bug_candidate | face 页 covered：`shots/mcp_face_reupload_generating_snapshot.md`；nose 测试服 Server busy 时错误显示 `Get It Now`：`shots/mcp_nose_generating_snapshot.md` |
| 8 | 分析结果图完成后优化区显示 `Generating optimized result...` | covered | `shots/mcp_face_predeploy_after_wait_snapshot.md` |
| 9 | SEO 配置字段驱动优化结果生成及 credits 扣减 | covered | `shots/mcp_face_continue_canvas_snapshot.md` 显示 credits 从成功生成后降至 760；`shots/mcp_face_mobile_continue_canvas_snapshot.md` 显示继续补测后降至 730；具体配置字段仅以页面行为验证，不做接口诊断 |
| 10 | 成功态 Upload Image 恢复可用并可重新生成 | covered | `shots/mcp_face_predeploy_success_snapshot.md`；`shots/mcp_face_reupload_generating_snapshot.md` |
| 11 | 分析结果图 Download 可下载 jpg | covered | MCP 下载事件 `pokecut-analysis-result-20260901-114118.jpg`；`shots/downloads/pokecut-analysis-result-20260901-114118.jpg`；nose 另有 `pokecut-analysis-result-20260901-114822.jpg` |
| 12 | 优化结果图 Download 可下载 jpg | covered | MCP 下载事件 `pokecut-optimized-result-20260901-114132.jpg`；`shots/downloads/pokecut-optimized-result-20260901-114132.jpg` |
| 13 | PC 成功态 Continue in Portrait Editor 带入三张图 | covered | `shots/mcp_face_continue_canvas_snapshot.md` 显示 图片 1/2/3；`shots/mcp_face_continue_canvas.png` 显示优化图选中和 Portrait Editor/Face 面板 |
| 14 | 分析服务器忙失败态 | covered | `shots/mcp_face_after_upload_snapshot.md`；`shots/mcp_face_retry_snapshot.md`；文案与按钮符合 |
| 15 | 移动端结果态纵向排版 | covered | `shots/mcp_face_mobile_success_snapshot.md`；`shots/mcp_face_mobile_success.png`；nose 证据 `shots/mcp_nose_mobile_result_snapshot.md` |
| 16 | 移动端成功态 Continue 仅携带优化结果图 | bug_candidate | `shots/mcp_face_mobile_continue_canvas_snapshot.md` 与 `.png` 显示实际带入 图片 1/2/3 三张图，非仅优化结果图 |

## 3. 需求差异
- **BUG-NOSE-001**：测试服 `nose-shape-detector` 在分析失败（Server busy）时，Optimized 区实际显示模糊承接和 `Get It Now`，且允许跳转画布；需求预期是分析结果未成功前优化区始终等待，页面不跳转无限画布。预部署分析成功后 `Get It Now` 承接本身正常。
- **BUG-FACE-MOBILE-001**：移动端 390x844 下 `ai-face-reader` 成功态点击 `Continue in Portrait Editor` 后，画布实际出现 图片 1/2/3 三张图，并选中优化结果图；需求预期移动端仅携带优化结果图进入 Portrait Editor。
- 已修正前次 blocked 项：`ai-face-reader` 成功三栏、下载 jpg、成功态 PC Continue、成功态 Upload Image 恢复均已通过预部署环境补充覆盖。
- 仍未覆盖：真实购买成功后回到结果页继续生成、网络错误、鉴黄失败、优化失败与 credits 扣返；这些需要支付链路授权或故障注入，本轮按纯 Playwright MCP 页面探索不执行。

## 4. 关键发现与下游注意事项
- 按 PROJECT.md 规则：测试服生成失败后，通过 `DEBUG` 面板选择 `预部署` 会刷新页面，必须重新登录后再上传；本轮成功态证据均来自预部署。
- `ai-face-reader` 成功态按钮选择器应按状态区分：生成中 `Upload Image` / Download / Continue disabled；成功后 `Upload Image`、两个 `Download`、`Continue in Portrait Editor` 均可点击。
- MCP 下载事件已验证 jpg 文件名：`pokecut-analysis-result-*.jpg` 与 `pokecut-optimized-result-*.jpg`；正式用例可断言下载扩展名和命名前缀。
- PC Continue 画布断言：URL 包含 `/agent?pid=`，snapshot 中出现 `图片 1` / `图片 2` / `图片 3`，优化图有选中框，Portrait Editor/Face 面板打开，`Generate` disabled 可作为未选模板的可观察证据。
- 移动端 Continue 是当前新增阻塞差异：后续 case-design 不应按需求直接断言通过，应等待 BUG-FACE-MOBILE-001 决策或将其作为失败用例。

## 5. 版本差异摘要
- `nose_shape_detector_v2.yaml` → `nose_shape_detector_v3.yaml`：补充预部署分析成功后的模糊承接、Analysis jpg 下载、成功后 `Get It Now` 进入画布仅带原图、Portrait Editor 面板与未选模板证据；保留测试服 Server busy 时 `Get It Now` 错误可用的 BUG-NOSE-001。
- `ai_face_reader_v2.yaml` → `ai_face_reader_v3.yaml`：补充预部署成功三栏、生成中二阶段、成功态 Upload Image 重传、Analysis/Optimized jpg 下载、PC Continue 带三图、移动端成功态与移动端 Continue 带图差异 BUG-FACE-MOBILE-001。

> confirmed 前不得进入 test-case-design。

