---
task_id: new_feature_detection_ui_20260901_124711
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  requirement_doc: "D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md"
  sync: artifacts/new_feature_detection_ui_20260901_124711/sync.md (confirmed 2026-09-02)
  page_maps:
    - page_map/pokecut/nose_shape_detector_v3.yaml
    - page_map/pokecut/ai_face_reader_v3.yaml
  environment: 测试服 pokecut-dev.guangzhuiyuan.com；测试服 Server busy 时按 PROJECT.md 切预部署并重新登录会员账号 450832596@qq.com
outputs:
  case_count: 2
  priority_breakdown: {P1: 2}
  execution_breakdown: {smoke: 2}
  reviewer_decision: 用户确认只保留 L6 用例，进入 test-writing
next_agent: test-writing
created_at: 2026-09-02 10:35:00 +08:00
updated_at: 2026-09-02 12:15:00 +08:00
---

# cases.md — 检测类功能适配 UI（final_after_sync · 仅 L6）

> 用户确认：本阶段只保留 L6 核心 Happy Path / E2E 用例，其余 L1~L5 用例不进入本任务脚本阶段（详见 `cases_full_matrix.md` 归档留痕）。`BUG-NOSE-001`、`BUG-FACE-MOBILE-001` 已由用户确认先 skip。

## 需求理解
检测类 SEO 工具页上传后进入结果编辑三栏。有优化结果图页面（ai-face-reader）成功态双图双下载 + PC Continue 带三图；无优化结果图页面（nose-shape-detector）成功态 Optimized 仅模糊承接 + Get It Now。生成与下载均需登录态；测试服失败时按 PROJECT.md 切预部署并重新登录。

## L6 核心 Happy Path / E2E（smoke）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L6-001 | P1 | face 全流程：登录→上传→双图生成→双下载→PC Continue | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop | 1. 预部署登录会员账号 450832596@qq.com；2. 打开 /tools/ai-face-reader；3. 上传 test_images/有人脸.JPG；4. 等待分析结果成功；5. 等待优化结果成功；6. 下载分析图；7. 下载优化图；8. 点击 Continue in Portrait Editor；9. 检查画布三图与面板 | 双图生成按预部署实际耗时轮询（最长 90s）；下载等事件；画布加载约 8s | 三栏成功态；两张 jpg 下载；Continue 后 /agent?pid= 带三图、优化图选中、Portrait Editor/Face 面板打开、Generate disabled | face_e2e_success.png, face_e2e_canvas.png |
| L6-002 | P1 | nose 全流程：登录→上传→分析成功→模糊承接→Get It Now | page_map/pokecut/nose_shape_detector_v3.yaml: states.predeploy_analysis_success_blur_desktop | 1. 预部署登录会员账号 450832596@qq.com；2. 打开 /tools/nose-shape-detector；3. 上传 test_images/有人脸.JPG；4. 等待分析成功；5. 点击 Get It Now；6. 检查画布承接 | 分析成功轮询（最长 90s）；画布加载约 8s | 分析结果图成功；Optimized 模糊承接 + Get It Now；画布仅原图、原图选中、Portrait Editor/Face 面板打开、Generate disabled | nose_e2e_blur.png, nose_e2e_canvas.png |

## page_ref 与 selector 表

| 用途 | page_map 引用 | 稳定 selector |
|---|---|---|
| 上传主按钮（两页） | v3 / v2 seo_default_desktop.buttons.upload_primary | text=Try Image to Image AI Now；input#img2imgFirstScreenUploadInput |
| 登录表单 | v2 modals.auth_modal | [data-testid="auth-email-input"] / [data-testid="auth-code-input"] / [data-testid="auth-submit"] |
| 原图区 Upload Image | v3 upload_image_enabled / upload_image_disabled | button:has-text("Upload Image") |
| 分析区 Download | v3 analysis_download | Analysis Result 区域 button:has-text("Download") |
| 优化区 Download | v3 optimized_download | Optimized Result 区域 button:has-text("Download") |
| Continue in Portrait Editor | v3 continue_portrait_pc | button:has-text("Continue in Portrait Editor") |
| Get It Now | v3 get_it_now_after_analysis_success | button:has-text("Get It Now") |
| DEBUG 面板环境切换 | v3 modals.debug_panel | button:has-text("DEBUG") → button:has-text("预部署") |

## 依赖缺口与风险
- 成功态证据依赖预部署环境：测试服持续 Server busy 时用例执行前需按 PROJECT.md 切预部署并重新登录会员账号 450832596@qq.com；切换环境后不得复用旧登录态。
- 已确认 skip：BUG-NOSE-001（nose 测试服分析失败时 Get It Now 错误可用）、BUG-FACE-MOBILE-001（face 移动端 Continue 带三图）——不写入本矩阵的通过断言。
- 未覆盖：网络错误、鉴黄失败、优化结果图失败、credits 不足购买成功、移动端优化失败承接、移动端成功 Continue 语义；均需故障注入或真实支付授权，或已确认 skip。
- L1~L5 完整矩阵见 `cases_full_matrix.md`（留痕），本任务脚本阶段仅执行 L6 两条 smoke。
