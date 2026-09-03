# Sync · Pokecut portrait detector representative pages（v2）

task_id: 2026-08-28_pokecut_portrait_detector_interactions
page_map: artifacts/2026-08-28_pokecut_portrait_detector_interactions/portrait_detector_pages_v2.yaml
legacy_page_map: artifacts/2026-08-28_pokecut_portrait_detector_interactions/portrait_detector_pages_v1.yaml
status: confirmed
next_agent: test-case-design
updated_at: 2026-08-28 22:20:00 +08:00

## 1. 探索摘要

- 范围：PC 1920x1080、en-US、预部署登录态；素材仅 test_images/有人脸.JPG。
- 结果态需「长等待」才会真实生成：Ethnicity ~47s、Body Shape ~30s、Face Comparison ~75s。
- 早期脚本因等待过短（5-9s）把 processing 误判为 result，本版已修正。
- 三页结果态控件一致：Download report、Upload another photo、Try My Photo（5-6 个）、Detector Dimension。
- Download report 触发 JPG 报告下载并弹出反馈问卷。
- Upload another photo（未保存时）触发 Unsaved Report 保存确认弹层。

## 2. 页面覆盖矩阵

| Page / State | 达成路径 | 覆盖结果 | 未覆盖原因 | 依赖条件 | 版本变化 |
|---|---|---:|---|---|---|
| 登录 / 测试服 | 上传触发 auth 后登录 | failed | authToken is empty / 网关 404 | - | v2 |
| 登录 / 预部署 | DEBUG 面板切预部署后登录 | completed | - | 账号/验证码 123456 | v2 |
| Ethnicity / 登录初始态 | 直连 /tools/ethnicity-guesser-ai | completed | - | 登录态 | v2 |
| Ethnicity / 上传自动出结果 | Upload Image -> 有人脸.JPG，~47s | completed | - | 登录态 | v2 |
| Body Shape / 上传 + Continue 出结果 | 三围 88/70/96 + 有人脸.JPG + Continue，~30s | completed | - | 登录态 | v2 |
| Face Comparison / A+B + Start 出结果 | A/B 有人脸.JPG + Start Comparison，~75s | completed | - | 登录态 | v2 |
| 结果态 Download report | 点击下载 JPG + 问卷 | completed | - | 结果态 | v2 |
| 结果态 Upload another photo | 点击弹 Unsaved Report 弹层 | completed | - | 结果态 | v2 |
| Unsaved Report 内 Download / Upload Without Saving | 点击两按钮 | completed | - | 结果态 | v2 |
| 反馈问卷 Submit / Maybe later | 点击两按钮 | completed | - | 下载后 | v2 |
| No Face Found / 多脸选择 | 需异常素材 | not_in_round | 本轮仅有人脸主路径 | 素材 | - |
| Try My Photo 各增强卡（body_shape 抽查 3 个） | 点击新开 /agent 画布页 | completed | - | 结果态 | v2 |

## 3. Requirement vs 实际（结果态）

| Requirement 点 | 覆盖结果 | 说明 |
|---|---|---|
| 结果态展示 Download report / Upload another photo | covered | 三页均出现这两个按钮 |
| Download report 下载报告 | covered | 下载 JPG：pokecut-body-shape-report-*.jpg / pokecut-face-comparison-report-*.jpg，随后弹问卷 |
| Upload another photo 重新上传 | covered | 点击后（未保存）弹 Unsaved Report（Download / Upload Without Saving） |
| 结果态增强建议 Try My Photo | covered | 三页均出现 5-6 个 Try My Photo 建议卡 |
| 结果态相似度/体型数值 | partially_covered | 结果以报告图（blob）呈现，数值断言需 OCR/视觉校验 |
| No Face Found / Change Photo / Cancel | not_in_round | 需无人脸素材 |
| 多脸选择弹层 / Photo A-B tab | not_in_round | 需多人脸素材 |

## 4. Bug candidates

### BUG-CANDIDATE-01 · 维度列表缺一句话描述（沿用 v1）
- Requirement：维度列表每项展示名称和一句话描述。
- Actual：10 个维度名称均存在，但未发现一句话描述。
- Evidence：dimension_switch_inventory.json / 04_dimension_dropdown_open.png
- Severity：needs_product_confirmation

### BUG-CANDIDATE-02 · 维度切换改变 SEO 原图与页面主体（沿用 v1）
- Requirement：维度切换不应改变 SEO 原图与页面主体。
- Actual：Ethnicity URL 切 Body Shape / Face Comparison 后原图变化，body hash 变化，URL 与 H1 不变。
- Evidence：dimension_switch_inventory.json / 05_dimension_after_body_shape.png / 06_dimension_after_face_comparison.png
- Severity：needs_product_confirmation

> 撤销说明：早期误报的「结果态控件缺失」「结果态残留处理态文案」两条 bug candidate 已撤销——系等待过短（5-9s）把 processing 误判为 result 所致；延长等待 30-75s 后三页均真实出结果且控件齐全。

## 5. 关键发现与下游注意事项

- 环境：测试服登录失败（authToken is empty / 网关 404，auth_login_debug_result.json）；预部署登录成功（auth_predeploy_result.json）；结果生成网关 http://10.17.1.64:8088/gateway/pokecut/api/...。
- 结果触发：Ethnicity 上传自动；Body Shape 必须点 Continue；Face Comparison 必须点 Start Comparison。
- 结果判定信号：button:has-text('Download report') 与 button:has-text('Upload another photo') 出现，且 body 不再含 Uploading Image / Detecting Image / Building Report。
- 结果态控件：
  - Download report -> JPG 下载 + 反馈问卷（Close / Q1 / Q2 / Q3 / Maybe later / Submit）。
  - Upload another photo -> 未保存时弹 Unsaved Report（Download / Upload Without Saving）。
  - Try My Photo（5-6 个）-> 增强建议卡；Face 另有 Tips For Becoming Better。
- 结果态交互实测（body_shape，代表其余两页）：
  - Unsaved Report 弹层 Download：下载 JPG 并关闭弹层留在结果态；之后再点 Upload another photo 直接回上传 UI（不再弹层）。
  - Unsaved Report 弹层 Upload Without Saving：返回上传输入 UI（URL 加 ?detectSeoV3EntryInputPicker=body_shape），不下载报告。
  - 问卷 Maybe later：关闭问卷并出现常驻 feedback 按钮；之后 Download report 不再弹问卷。
  - 问卷 Submit（空选项）：无可见效果，问卷保持打开（疑需先作答 Q1/Q2/Q3）。
  - Try My Photo（抽查 3 个）：点击新开标签页进入 /agent?pid=... 画布页（Free Infinite Canvas），预选对应增强工具（Clothes Changer / Hairstyle / Body 等），主页面 URL 与结果态不变。
- 素材约束：上传仅限 test_images/；本轮只用有人脸.JPG。
- 控制台噪声：hydration mismatch、偶发 500/ERR_CONNECTION_TIMED_OUT，不影响结果渲染；回归脚本避免误判失败。

## 6. 状态与按钮覆盖摘要

- 三页结果态控件均已捕获；Download report / Upload another photo / Try My Photo 已在 body_shape 实测（代表三页）。
- 下载文件名规律：pokecut-<page>-report-<timestamp>.jpg。
- 问卷弹层与 Unsaved Report 弹层的按钮已点击（body_shape）：Download / Upload Without Saving / Maybe later / Submit（空提交无效果）。

## 7. 版本差异摘要

- v1 -> v2 新增：登录/服务器切换、三页登录态/上传/processing/结果态、结果态控件与弹层。
- v2 修正：结果态等待时长与控件（Download report / Upload another photo / Try My Photo）；撤销早期两条误报 bug candidate。

> 在本文档 confirmed 之前，不得进入 test-case-design。

## 8. 待用户确认

1. 结果态数值（体型/相似度/种族占比）以图片呈现，是否接受用 OCR/视觉校验而非 DOM 文本断言。
2. 是否需要继续补 No Face Found / 多脸选择 / Unsaved Report 两按钮 / 问卷提交等异常与结果态按钮逐项探索。
3. 是否接受「测试服失败 -> 预部署登录」作为结果态生成的环境结论。

## 9. 证据清单

- 测试服登录失败：auth_login_debug_result.json
- 预部署登录成功：auth_predeploy_result.json
- 结果态证据 v5：result_states_v5_inventory.json / result_states_v5_summary.json
- 关键截图：45_ethnicity_result.png、45_body_result.png、45_face_result.png（及 *_result_full.png）、46_after_upload_another.png、45_body_after_download.png
- 结果态交互证据：result_actions_inventory.json / result_actions2_inventory.json / result_actions3_inventory.json（及对应 summary）
- 关键截图：47_*（Try My Photo / 问卷）、48_*（Try My Photo 正确点击 / Submit / Upload Without Saving）、49_*（Submit 空提交）
- 早期证据（已被 v5 覆盖，仅作历史）：result_states_v2_*.json、result_states_v3_*.json
