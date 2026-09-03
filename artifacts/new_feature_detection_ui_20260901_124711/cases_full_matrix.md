---
task_id: new_feature_detection_ui_20260901_124711
agent: test-case-design
phase: final_after_sync
status: archived_l6_only
note: 完整 28 条矩阵留痕。用户确认本任务脚本阶段只执行 L6 两条 smoke；本文件仅存档不用于执行。
inputs:
  requirement_doc: "D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md"
  sync: artifacts/new_feature_detection_ui_20260901_124711/sync.md (confirmed 2026-09-02)
  page_maps:
    - page_map/pokecut/nose_shape_detector_v3.yaml
    - page_map/pokecut/ai_face_reader_v3.yaml
    - page_map/pokecut/nose_shape_detector_v2.yaml
    - page_map/pokecut/ai_face_reader_v2.yaml
  environment: 测试服 pokecut-dev.guangzhuiyuan.com；测试服 Server busy 时按 PROJECT.md 切预部署并重新登录会员账号 450832596@qq.com
outputs:
  case_count: 28
  priority_breakdown: {P0: 0, P1: 15, P2: 13}
  execution_breakdown: {smoke: 2, regression: 5, default_full: 21}
  skipped_by_user:
    - BUG-NOSE-001
    - BUG-FACE-MOBILE-001
next_agent: null (archived; execution uses cases.md L6 only)
created_at: 2026-09-02 10:35:00 +08:00
updated_at: 2026-09-02 12:34:00 +08:00
---

# cases.md 完整矩阵（28 条，已归档） — 检测类功能适配 UI

> 本文件为完整 L1~L6 矩阵留痕。用户确认本任务脚本阶段只保留 L6（见 `cases.md`），本文件不用于执行。

## 需求理解
检测类 SEO 工具页上传后进入结果编辑三栏（Original Image / Analysis Result / Optimized Result）。有优化结果图页面（ai-face-reader）成功态双图双下载 + PC Continue 带三图；无优化结果图页面（nose-shape-detector）成功态 Optimized 仅模糊承接 + Get It Now。失败逻辑覆盖网络错误 / 服务器忙 / 鉴黄 / 优化失败；购买逻辑覆盖 credits 不足弹窗与承接；移动端纵向排版且 Continue 仅带优化图（存在 BUG-FACE-MOBILE-001，用户确认 skip）。生成与下载均需登录态；测试服失败时按 PROJECT.md 切预部署并重新登录。

## L1 页面元素 / 结构（regression）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L1-001 | P1 | 上传前保持原 SEO 内容结构和文案（nose） | page_map/pokecut/nose_shape_detector_v2.yaml: states.seo_default_desktop | 1. 打开 /tools/nose-shape-detector；2. 检查首屏 H1、描述、示例图、上传框、Terms/Privacy；3. 检查是否出现结果编辑三栏 | 等待 CSR 渲染完成 | H1 包含 Free AI Nose Shape Detector；上传框可见；不出现三栏标题 | nose_seo_default.png |
| L1-002 | P1 | 上传前保持原 SEO 内容结构和文案（face） | page_map/pokecut/ai_face_reader_v2.yaml: states.seo_default_desktop | 1. 打开 /tools/ai-face-reader；2. 检查首屏 H1、描述、上传框与示例图；3. 检查是否出现三栏 | 等待 CSR 渲染完成 | H1 包含 AI Face Reader；上传框可见；不出现三栏标题 | face_seo_default.png |
| L1-003 | P1 | 有优化结果图页面成功态展示三栏结果态 | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop | 1. 预部署登录会员账号；2. 上传 test_images/有人脸.JPG；3. 等待双图成功；4. 检查三栏标题与区域 | 等待 Optimized Result img 出现 | 从左至右出现三栏；三区均有真实 img；两个 Download + Continue | face_success_three_columns.png |
| L1-004 | P1 | 无优化结果图页面展示模糊承接态 | page_map/pokecut/nose_shape_detector_v3.yaml: states.predeploy_analysis_success_blur_desktop | 1. 预部署登录；2. 上传 test_images/有人脸.JPG；3. 等待分析成功；4. 检查 Optimized 区域结构 | 等待分析 img 与承接文案 | Optimized 显示模糊承接图、固定文案、Get It Now；无 Download | nose_blur_placeholder.png |
| L1-005 | P2 | 分析服务器忙失败态结构（face） | page_map/pokecut/ai_face_reader_v2.yaml: states.analysis_server_busy_desktop | 1. 测试服登录；2. 上传触发 Server busy；3. 检查失败态结构 | 等待失败文案 | Server busy 文案；Change Image/Try again；Optimized 等待态 | face_server_busy_structure.png |

## L2 交互行为 / 状态迁移（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L2-001 | P1 | 上传后进入生成中状态 | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_reupload_generating_desktop | 1. 预部署登录；2. Upload Image 选 test_images/多人脸.jpg；3. 观察三区 | 点击后立即采样 | 新缩略图 + Upload disabled；Generating analysis... + Download disabled；Waiting for analysis... | face_generating_state.png |
| L2-002 | P1 | 分析成功后优化加载态 | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop | 1. 预部署上传；2. 分析成功、优化未完成时采样 | 轮询 | 分析 img 可见；Generating optimized result...；按钮 disabled | face_optimized_generating.png |
| L2-003 | P1 | 成功态 Upload Image 恢复并重传 | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop.buttons.upload_image_enabled | 1. 预部署完成双图；2. Upload Image 选 test_images/多人脸.jpg | 等待文件选择器 | 可点并打开选择器；重传进入生成中态 | face_reupload_flow.png |
| L2-004 | P1 | 分析图 Download 下载 jpg | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop.buttons.analysis_download | 1. 预部署完成双图；2. 点击 Analysis Download | 等待下载事件 | 文件名匹配 pokecut-analysis-result-*.jpg | face_analysis_download.png |
| L2-005 | P1 | 优化图 Download 下载 jpg | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop.buttons.optimized_download | 1. 预部署完成双图；2. 点击 Optimized Download | 等待下载事件 | 文件名匹配 pokecut-optimized-result-*.jpg | face_optimized_download.png |
| L2-006 | P1 | PC Continue 带入三张图 | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop.buttons.continue_portrait_pc | 1. 预部署完成双图；2. 点击 Continue；3. 检查画布 | 画布加载约 8s | /agent?pid=；图片 1/2/3；优化图选中；Portrait Editor/Face 面板；Generate disabled | face_continue_canvas.png |
| L2-007 | P1 | nose Get It Now 进入画布选中原图 | page_map/pokecut/nose_shape_detector_v3.yaml: states.predeploy_analysis_success_blur_desktop.buttons.get_it_now_after_analysis_success | 1. 预部署完成分析；2. 点击 Get It Now；3. 检查画布 | 画布加载约 8s | /agent?pid=；仅图片 1；原图选中；Portrait Editor/Face 面板；Generate disabled | nose_getitnow_canvas.png |
| L2-008 | P2 | 失败态 Try again 重试 | page_map/pokecut/ai_face_reader_v2.yaml: states.analysis_server_busy_desktop.buttons.try_again | 1. 测试服触发 Server busy；2. 点击 Try again | 等待状态更新 | 状态刷新；失败态可再次出现；Download disabled | face_try_again.png |
| L2-009 | P2 | 失败态 Change Image 重走流程 | page_map/pokecut/ai_face_reader_v2.yaml: states.analysis_server_busy_desktop.buttons.change_image | 1. 测试服触发 Server busy；2. 点击 Change Image 选图 | 等待文件选择器 | 弹出选择器；重新走分析流程 | face_change_image.png |
| L2-010 | P2 | 移动端结果态纵向排版（face） | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_mobile | 1. viewport 390x844；2. 预部署上传并等待双图 | 等待 Optimized img | 从上到下三栏；文案与 PC 一致 | face_mobile_vertical.png |

## L3 异常 / 权限 / 兼容（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L3-001 | P1 | 分析服务器忙失败态完整验证 | page_map/pokecut/ai_face_reader_v2.yaml: states.analysis_server_busy_desktop | 1. 测试服登录；2. 上传触发 Server busy；3. 记录 credits 变化 | 等待失败文案 | Server busy 文案；Change Image/Try again；Optimized 等待；不扣 credits | face_server_busy_full.png |
| L3-002 | P2 | 分析网络错误失败态 | TBD（需网络故障注入） | 1. 注入网络错误；2. 上传；3. 观察 | 等待 Network error 文案 | Network error, please try again；Change Image/Try again | skipped 未执行 |
| L3-003 | P2 | 分析鉴黄失败态 | TBD（需鉴黄故障注入） | 1. 触发鉴黄失败；2. 观察 | 等待 Policy violation 文案 | Policy violation...；仅 Change Image；不扣 credits | skipped 未执行 |
| L3-004 | P2 | 优化结果图生成失败态 | TBD（需优化故障注入） | 1. 触发优化失败；2. 观察 | 等待 Optimization failed 文案 | Optimization failed...；仅 Portrait Editor；credits 返还 | skipped 未执行 |
| L3-005 | P2 | 分析 credits 不足购买弹窗并恢复生成 | TBD（需购买授权） | 1. credits 不足账号触发分析；2. 购买；3. 回结果页 | 等待购买弹窗 | 购买弹窗；购买成功回结果页继续生成 | skipped 未执行 |
| L3-006 | P2 | 优化 credits 不足模糊承接并进入后续链路 | page_map/pokecut/nose_shape_detector_v3.yaml: states.predeploy_analysis_success_blur_desktop | 1. 触发优化 credits 不足（无法注入则以 nose 无优化图承接等价验证）；2. 点击 Get It Now | 等待承接文案 | 模糊承接 + Get It Now；点击进入 Portrait Editor 承接 | nose_credit_shortfall_blur.png |
| L3-007 | P2 | 移动端优化失败仅带原图 | TBD（需优化故障注入） | 1. 移动端触发优化失败；2. 点击 Portrait Editor | 等待画布 | 仅带原图；选中原图；功能弹窗 | skipped 未执行 |

## L4 PRD AC 逐条映射（regression）

| AC | 摘要 | 覆盖用例 | 期望/缺口 |
|---|---|---|---|
| 1 | 上传前保持原 SEO 内容结构和文案 | L1-001, L1-002 | 符合 |
| 2 | 有优化结果图页面成功态展示三栏 | L1-003, L2-006 | 符合 |
| 3 | 无优化结果图页面展示模糊承接态 | L1-004, L2-007 | 符合 |
| 4 | Get It Now 进入 Portrait Editor 承接 | L2-007, L6-002 | 符合 |
| 5 | 生成中原图缩略图 + Upload Image 不可点击 | L2-001 | 符合 |
| 6 | 分析生成中 Generating analysis... | L2-001 | 符合 |
| 7 | 分析未成功前优化区保持 Waiting | L2-001, L3-001 | 缺口：BUG-NOSE-001（用户确认 skip） |
| 8 | 分析成功后优化区 Generating optimized result... | L2-002 | 符合 |
| 9 | SEO 配置字段驱动优化生成及 credits 扣减 | L2-005, L6-001 | 页面行为验证通过；配置取值需后端提供 |
| 10 | 成功态 Upload Image 恢复可用并重传 | L2-003 | 符合 |
| 11 | 分析结果图 Download 下载 jpg | L2-004 | 符合 |
| 12 | 优化结果图 Download 下载 jpg | L2-005 | 符合 |
| 13 | PC Continue 带入三张图 | L2-006, L6-001 | 符合 |
| 14 | 分析网络错误失败态 | L3-002 | skipped（无故障注入） |
| 15 | 分析服务器忙失败态 | L3-001, L2-008, L2-009 | 符合；不扣 credits |
| 16 | 分析鉴黄失败态 | L3-003 | skipped（无故障注入） |
| 17 | 优化结果图生成失败态 | L3-004, L3-007 | skipped（无故障注入） |
| 18 | 分析 credits 不足购买弹窗并恢复生成 | L3-005 | skipped（未授权支付） |
| 19 | 优化 credits 不足模糊承接并进入后续链路 | L3-006 | 等价路径 covered |
| 20 | 移动端结果态纵向排版 | L2-010, L6-001 | 符合 |
| 21 | 移动端成功态 Continue 仅带优化图；失败态仅带原图 | L2-010, L3-007 | 缺口：BUG-FACE-MOBILE-001（用户确认 skip） |

## L5 数据边界与等价类（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L5-001 | P2 | 图片格式等价类 JPG/PNG/WebP | page_map/pokecut/ai_face_reader_v2.yaml: states.seo_default_desktop.buttons.upload_primary | 1. 预部署登录；2. 分别上传 有人脸.JPG / 4K.png / eac4b74543a98226cffc75f1f1d4ae014a90f703bd95.webp；3. 等待结果 | 每次等缩略图 | 三格式均进入结果态 | format_jpg.png, format_png.png, format_webp.png |
| L5-002 | P2 | 不支持/损坏图片上传校验 | page_map/pokecut/ai_face_reader_v2.yaml: states.seo_default_desktop | 1. 上传 test_images/损坏的图.png；2. 观察 | 等待上传反馈 | 格式/上传失败提示或阻止进入生成 | upload_invalid.png |
| L5-003 | P2 | 人脸数量等价类 单人/多人/无人 | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop | 1. 分别上传 有人脸.JPG / 多人脸.jpg / 无人脸.jpg | 每次等结果 | 单人/多人可分析；无人脸按页面实际行为 | face_single.png, face_multi.png, face_none.png |
| L5-004 | P2 | 分辨率等价类 低分辨率/1K/4K/8K | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop | 1. 分别上传 低分辨率.JPG / 1K.jpg / 4K.jpg / 8K.jpg | 每次等结果 | 各分辨率可进入结果态；8K 不崩溃 | res_low.png, res_1k.png, res_4k.png, res_8k.png |

## L6 核心 Happy Path / E2E（smoke）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L6-001 | P1 | face 全流程：登录→上传→双图生成→双下载→PC Continue | page_map/pokecut/ai_face_reader_v3.yaml: states.predeploy_success_three_columns_desktop | 1. 预部署登录会员账号 450832596@qq.com；2. 打开 /tools/ai-face-reader；3. 上传 test_images/有人脸.JPG；4. 等待分析成功；5. 等待优化成功；6. 下载分析图；7. 下载优化图；8. 点击 Continue in Portrait Editor；9. 检查画布三图与面板 | 双图生成轮询（最长 90s）；画布约 8s | 三栏成功态；两张 jpg；Continue 后三图、优化图选中、Portrait Editor/Face 面板、Generate disabled | face_e2e_success.png, face_e2e_canvas.png |
| L6-002 | P1 | nose 全流程：登录→上传→分析成功→模糊承接→Get It Now | page_map/pokecut/nose_shape_detector_v3.yaml: states.predeploy_analysis_success_blur_desktop | 1. 预部署登录会员账号 450832596@qq.com；2. 打开 /tools/nose-shape-detector；3. 上传 test_images/有人脸.JPG；4. 等待分析成功；5. 点击 Get It Now；6. 检查画布承接 | 分析成功轮询（最长 90s）；画布约 8s | 分析图成功；模糊承接 + Get It Now；画布仅原图、原图选中、Portrait Editor/Face 面板、Generate disabled | nose_e2e_blur.png, nose_e2e_canvas.png |

## page_ref 与 selector 表
| 用途 | page_map 引用 | 稳定 selector |
|---|---|---|
| 上传主按钮（两页） | v2 seo_default_desktop.buttons.upload_primary | text=Try Image to Image AI Now；input#img2imgFirstScreenUploadInput |
| 登录表单 | v2 modals.auth_modal | [data-testid="auth-email-input"] / [data-testid="auth-code-input"] / [data-testid="auth-submit"] |
| 原图区 Upload Image | v3 upload_image_enabled / upload_image_disabled | button:has-text("Upload Image") |
| 分析区 Download | v3 analysis_download | Analysis Result 区域 button:has-text("Download") |
| 优化区 Download | v3 optimized_download | Optimized Result 区域 button:has-text("Download") |
| Continue in Portrait Editor | v3 continue_portrait_pc / continue_portrait_mobile | button:has-text("Continue in Portrait Editor") |
| Get It Now | v3 get_it_now_after_analysis_success | button:has-text("Get It Now") |
| 失败态按钮 | v2 change_image / try_again | button:has-text("Change Image") / button:has-text("Try again") |
| DEBUG 面板环境切换 | v3 modals.debug_panel | button:has-text("DEBUG") → button:has-text("预部署") |

## 依赖缺口与风险
- 成功态证据依赖预部署环境；测试服持续 Server busy 时切预部署并重新登录会员账号。
- 已确认 skip：BUG-NOSE-001、BUG-FACE-MOBILE-001。
- 未覆盖：网络错误、鉴黄、优化失败、credits 购买成功、移动端优化失败承接；需故障注入或真实支付授权。
- 素材限制：test_images 无 BMP；L5-001 仅覆盖 JPG/PNG/WebP。
- PRD-only 缺口：extendFunType / extendPresetParams 配置取值与 credits 扣减数值未提供。
