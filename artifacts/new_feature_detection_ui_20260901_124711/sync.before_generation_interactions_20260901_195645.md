---
task_id: new_feature_detection_ui_20260901_124711
agent: page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: false
inputs:
  - D:\downloads\用例\task-39-飞书文档_ 检测类功能适配UI需求文档 (1)\检测类功能适配UI需求文档.md
  - https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
  - https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader
  - driver: playwright_mcp_only
outputs:
  scanned_pages: [/tools/nose-shape-detector, /tools/ai-face-reader, /agent?pid=<uuid>]
  page_map_versions: [nose_shape_detector_v2.yaml, ai_face_reader_v2.yaml]
  coverage_gates: {mcp_connectivity: covered, desktop_initial: covered, desktop_upload_error_state: covered, nose_blur_placeholder: covered, nose_get_it_now_canvas: covered, mobile_nose_result_layout: covered, face_success_state: blocked_by_dependency, downloads: blocked_by_dependency, success_continue_portrait_editor: blocked_by_dependency}
  state_button_coverage: "covered: upload/login/failure/retry/disabled/download-placeholder/Get It Now；blocked: success download/continue/upload-enabled"
  requirement_actual_diffs:
    - {case: "nose 分析失败前优化区等待态", diff_type: bug_candidate, detail: "Analysis Result 已显示 Server busy 时，Optimized Result 仍显示模糊承接和 Get It Now，且点击可跳转 /agent?pid=...；预期为 Waiting for analysis... 且不跳转"}
    - {case: "ai-face-reader 成功三栏/下载/Continue", diff_type: skipped, detail: "测试服后端持续 Server busy，未进入成功态；纯 MCP 不做 mock/故障注入，因此成功图、jpg 下载和成功态 Continue 未覆盖"}
  bug_candidates:
    - {id: BUG-NOSE-001, severity: high, page: /tools/nose-shape-detector, detail: "分析失败时 Optimized Result 错误展示 Get It Now 并允许进入画布"}
  skipped:
    - {item: "ai-face-reader 成功态三栏真实图", reason: "后端生成持续 Server busy"}
    - {item: "分析/优化结果图 jpg 下载", reason: "未进入成功态，Download disabled"}
    - {item: "成功态 Continue in Portrait Editor", reason: "未进入成功态，Continue disabled"}
    - {item: "网络错误/鉴黄/优化失败/credits 扣返故障注入", reason: "本次限定纯 Playwright MCP，未授权 mock/DevTools/支付链路"}
  special_dependencies: ["后端生成服务恢复后需补测成功态", "真实购买/订阅链路未授权不执行", "测试素材限定 test_images/ 有人脸.JPG"]
  specs_updated: false
next_agent: null
created_at: 2026-09-01 14:36:00 +08:00
---

# sync.md — 检测类功能适配 UI 纯 MCP 探索

## 1. 探索摘要
- MCP 连通性已先验证：Playwright MCP 成功打开 `https://pokecut-dev.guangzhuiyuan.com/`，随后全程使用 MCP 的 navigate / snapshot / click / file_upload / resize / screenshot 进行探索。
- `nose-shape-detector` 默认态保持 SEO 首屏结构：H1、描述、示例图、上传框、Terms/Privacy、下方 SEO 内容均可见，未出现结果编辑三栏。
- `ai-face-reader` 默认态同样保持 SEO 首屏结构，未出现 `Original Image` / `Analysis Result` / `Optimized Result` 三栏。
- 登录会员账号 `450832596@qq.com` 后上传 `D:\Test\web-test\test_images\有人脸.JPG`；两个页面均进入三栏容器，但测试服分析生成均返回 `Server busy. We're fixing it now. No credits deducted.`。
- `ai-face-reader` 的服务器忙失败态符合需求：Analysis 区出现 `Change Image` / `Try again`，Download disabled；Optimized 区保持 `Waiting for analysis...`，Download 与 `Continue in Portrait Editor` disabled。
- `nose-shape-detector` 出现候选缺陷：分析失败时 Optimized 区没有保持等待态，而是展示模糊承接文案和 `Get It Now`；点击后可进入 `/agent?pid=...` 并打开 Portrait Editor/Face 面板。
- 移动端 390x844 已复测 `nose-shape-detector`，三块区域纵向排列，但同样复现分析失败时展示 `Get It Now` 的问题；`ai-face-reader` 成功移动态因后端阻塞未重复探索。

## 2. 页面覆盖矩阵（对照需求 16 条 AC）
| # | 用例/覆盖点 | 结论 | 证据 |
|---|---|---|---|
| 1 | 上传前保持原 SEO 内容结构和文案 | covered | `shots/mcp_nose_default_snapshot_deep.md`；`shots/mcp_face_default_snapshot.md` |
| 2 | 有优化结果图页面成功态展示三栏结果态 | skipped | `shots/mcp_face_after_upload_snapshot.md`：已出现三栏容器，但后端 Server busy，未得到成功图 |
| 3 | 无优化结果图页面展示模糊承接态 | covered | `shots/mcp_nose_result_server_busy_blur.png`；但触发时机存在 BUG-NOSE-001 |
| 4 | 点击 nose `Get It Now` 进入 Portrait Editor 承接 | covered | `shots/mcp_nose_getitnow_canvas.png`；URL `/agent?pid=...`，原图图层选中，Portrait Editor/Face 面板打开 |
| 5 | 结果生成中原图展示缩略图且 Upload Image 不可点击 | covered | `shots/mcp_face_after_upload_snapshot.md`；`shots/mcp_nose_generating_snapshot.md` |
| 6 | 分析生成中灰色蒙层/`Generating analysis...` | skipped | MCP 采样时已直接进入 Server busy，未捕获中间 loading 文案 |
| 7 | 分析未成功前优化区保持 `Waiting for analysis...` | gap / bug_candidate | face 页符合；nose 页失败时展示 `Get It Now` 并可跳转画布 |
| 8 | 分析结果图完成后优化区显示 `Generating optimized result...` | skipped | 后端未返回分析成功图，无法进入优化生成中 |
| 9 | SEO 配置字段驱动优化结果生成及 credits 扣减 | skipped | 需后端成功态/credits 配置证据；纯 MCP 不做接口诊断 |
| 10 | 成功态 Upload Image 恢复可用 | skipped | 未进入成功态；当前失败态 Upload Image disabled |
| 11 | 分析结果图 Download 可下载 jpg | skipped | 未进入成功态；Analysis Download disabled |
| 12 | 优化结果图 Download 可下载 jpg | skipped | 未进入成功态；Optimized Download disabled / nose 无优化下载按钮 |
| 13 | 成功态 Continue in Portrait Editor 带入三张图 | skipped | ai-face-reader 未进入成功态，Continue disabled |
| 14 | 分析服务器忙失败态 | covered | `shots/mcp_face_after_upload_snapshot.md`；`shots/mcp_face_retry_snapshot.md`；文案与按钮符合 |
| 15 | 移动端结果态纵向排版 | covered | `shots/mcp_nose_mobile_result_snapshot.md`；`shots/mcp_nose_mobile_result.png` |
| 16 | 移动端成功态 Continue 仅携带优化结果图 | skipped | 后端成功态阻塞，未覆盖 |

## 3. 需求差异
- 阻塞级候选缺陷：`nose-shape-detector` 在分析失败（Server busy）时，Optimized 区实际显示模糊承接和 `Get It Now`，且允许跳转画布；需求预期是分析结果未成功前优化区始终等待，页面不跳转无限画布。
- 覆盖受限差异：`ai-face-reader` 成功态三栏真实图片、两个 jpg 下载、成功态 Continue 携带三图均因测试服后端持续 `Server busy` 未覆盖；探索阶段不能把后端依赖问题伪装为 covered。
- 采样受限差异：`Generating analysis...`、`Generating optimized result...` 属短暂中间态，本轮 MCP 采样未捕获，后续若后端恢复建议用自动化轮询补证。

## 4. 关键发现与下游注意事项
- 本次用户要求“纯 MCP 探索”，因此所有页面证据来自 Playwright MCP；没有使用 DevTools trace、接口 mock、脚本注入故障或真实支付链路。
- 免费新账号注册后会弹出积分/购买相关弹窗，可能遮挡上传区；会员账号 `450832596@qq.com` 登录后可稳定进入上传流程。
- 上传按钮可通过文本 `Try Image to Image AI Now` 打开 MCP file chooser；直接点击隐藏的 `#img2imgFirstScreenUploadInput` 会被 label/header 或弹窗遮挡，不适合沉淀为正式点击路径。
- `ai-face-reader` 的 Server busy 失败态可作为后续异常态用例：断言文案、`Change Image` / `Try again`、Download disabled、Optimized 等待态与 Continue disabled。
- `nose-shape-detector` 的 `Get It Now` 跳转画布已可达，但当前可达时机不正确；建议先确认 BUG-NOSE-001 是否作为阻塞缺陷处理，再决定是否进入 case-design。

## 5. 版本差异摘要
- `nose_shape_detector_v1.yaml` → `nose_shape_detector_v2.yaml`：补充纯 MCP 下的 SEO 默认态、登录上传后 Server busy + blur 承接、`Get It Now` 画布承接、移动端纵向复现状态，并标记 BUG-NOSE-001。
- `ai_face_reader_v1.yaml` → `ai_face_reader_v2.yaml`：补充纯 MCP 下的 SEO 默认态、上传/示例图触发三栏、Server busy 失败态、Download/Continue disabled，以及成功态 blocked_by_dependency 按钮定义。

> confirmed 前不得进入 test-case-design。
