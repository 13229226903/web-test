---
task_id: 2026-08-28_pokecut_portrait_detector_interactions
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  - artifacts/2026-08-28_pokecut_portrait_detector_interactions/requirement.md
  - artifacts/2026-08-28_pokecut_portrait_detector_interactions/sync_v2.md
  - artifacts/2026-08-28_pokecut_portrait_detector_interactions/portrait_detector_pages_v2.yaml
outputs:
  case_count: 14
  priority_breakdown: {P0: 6, P1: 7, P2: 1}
next_agent: test-writing
created_at: 2026-08-29 11:00:00 +08:00
updated_at: 2026-08-29 13:10:00 +08:00
---

# 测试用例 — 人像检测类三入口页（Ethnicity / Body Shape / Face Comparison）

> 阶段 final_after_sync。page_ref 指向 `portrait_detector_pages_v2.yaml`（v1 仅匿名态参考）。
> 需求第 2、第 3 点文案未更新，以实际页面为准。

## 需求理解

- PRD：`requirement.md`（人像检测类进一步优化与实验需求大纲）。
- 环境：`http://10.17.1.66:3001` 预部署；PC 1920x1080 en-US；账号 `450832596@qq.com` / 验证码 `123456`；测试服优先，失败切预部署并登录。
- 三入口：`/tools/ethnicity-guesser-ai`、`/tools/body-shape-detector`、`/tools/face-comparison`。
- 素材仅 `test_images/`：`有人脸.JPG`、`多人脸.jpg`、`无人脸.jpg`、`损坏的图.png`、`1K.jpg`。

### 状态机（结果态）
`upload -> processing（Uploading/Detecting/Building Report）-> result（出现 Download report / Upload another photo / Try My Photo，且 processing 文案消失）`
- Ethnicity：上传自动触发，约 47s。
- Body Shape：上传照片 + 点 `Continue`，约 30s。
- Face Comparison：A/B 双图 + 点 `Start Comparison`，约 75s。

### 异常 / 权限 / 风险
- 匿名上传弹 auth modal（`[data-testid=auth-dialog]`）。
- 测试服登录失败（authToken is empty / 网关 404），需切预部署。
- 控制台 hydration mismatch / 偶发 500 / 超时：非阻塞，回归不判失败。
- 结果生成消耗 credits（账号 credits 9740），脚本需控制生成次数。

## L2 交互行为 / 状态迁移（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|:---:|---|---|---|---|---|
| TC-POR-L2-001 | P1 | 维度切换 + 下拉 10 项 | pages.<pg>.states.logged_in_initial.buttons.detector_dimension | 展开下拉断言 10 项名称，再选择 Body/Face 再恢复 | 文案/aria-expanded 变化 | 展开后 10 项齐全；选中维度更新；URL 与 H1 不变；原图变化记 bug candidate 02 | 切换前/后 |
| TC-POR-L2-002 | P1 | 上传缩略图 + Re-upload/Delete | pages.body_shape_detector.states.upload_thumbnail / face_comparison.states.upload_thumbnail | Body/Face 上传后观察 | 缩略图出现 | Re-upload photo / Delete uploaded photo 可见；点 Re-upload 打开 file chooser | 上传后 |
| TC-POR-L2-003 | P0 | Ethnicity 首屏结构 + 上传自动出结果 | pages.ethnicity_guesser.states.result | 断言 h1 / Upload Image / Private by default；Upload Image 选有人脸.JPG | 等 `button:has-text('Download report')` ≤120s | 结果态出现，processing 文案消失 | 上传前/生成中/结果 |
| TC-POR-L2-004 | P0 | Body 首屏结构 + 上传+Continue 出结果 | pages.body_shape_detector.states.result | 断言 h1 + 三围输入存在；填 88/70/96，Upload Photo 选有人脸.JPG，点 Continue | 等 Download report ≤90s | 结果态出现 | 上传前/Continue 后/结果 |
| TC-POR-L2-005 | P0 | Face 首屏结构 + 双图+Start 出结果 | pages.face_comparison.states.result | 断言 h1 + Upload Photo A/B + Start Comparison；Upload Photo A/B 选有人脸.JPG，点 Start Comparison | 等 Download report ≤120s | 结果态出现 | 双图/Start 后/结果 |
| TC-POR-L2-006 | P0 | Download report→下载+问卷 | result_state_common.result_controls.download_report + shared_states.download_questionnaire | 结果态点 Download report；问卷内点 Maybe later；再点 Download report 看是否复弹 | expect_download + 弹层变化 | 下载 JPG（pokecut-<page>-report-*.jpg）；问卷含 Close/Q1/Q2/Q3/Maybe later/Submit；Maybe later 关闭并出现 feedback、之后不再弹问卷 | 点击后 |
| TC-POR-L2-007 | P0 | Upload another photo→Unsaved Report | shared_states.unsaved_report_modal | 结果态点 Upload another photo；弹层内先 Download；再点 Upload another photo 后点 Upload Without Saving | expect_download / URL 变化 | Download 下载 JPG 并关闭留结果态；之后直接回上传 UI；Upload Without Saving 返回上传 UI（URL 含 detectSeoV3EntryInputPicker） | 点击前后 |
| TC-POR-L2-008 | P0 | Try My Photo→新开 /agent 画布 | pages.body_shape_detector.states.result.buttons.try_my_photo | 点第 1/2/3 个 Try My Photo | expect_popup + domcontentloaded | 新开标签页 URL 匹配 `/agent?pid=...`，title 含 Free Infinite Canvas；主页面 URL 与结果态不变 | 点击前/新标签页 |

## L3 异常 / 权限 / 兼容（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 期望 |
|---|---|:---:|---|---|---|
| TC-POR-L3-001 | P1 | 匿名上传 auth wall | shared_states.anonymous_upload_auth_modal（v1） | 未登录点上传选文件 | 弹 auth modal（email/code/submit）；Escape 不关闭 |
| TC-POR-L3-002 | P1 | Face 空/单图 Start Comparison toast | pages.face_comparison.states.logged_in_initial.buttons.start_comparison | 空态与仅 A 图各点一次 | toast `Please upload two photos before starting the comparison.`；不进入处理 |
| TC-POR-L3-003 | P2 | Body 无照片点 Continue | pages.body_shape_detector.states.logged_in_initial.buttons.continue | 只填三围点 Continue | 不进入 processing（保持介绍态，无 loading） |
| TC-POR-L3-004 | P1 | 无人脸 → No Face Found 弹层 | shared_states.noface_dialog | 上传 无人脸.jpg | 弹层 role=dialog：No Face Found / Please choose another photo with a clear single face. / Change Photo / Cancel；Change Photo 打开 file chooser；Cancel 关闭返回上传态 |
| TC-POR-L3-005 | P1 | 多人脸 → Choose a Face 弹层 + 提交 | shared_states.multiface_popup | 上传 多人脸.jpg | 弹层 Choose a Face to Analyze；Select face N 按钮；选中 aria-pressed=true + 实线绿框，未选中 aria-pressed=false + 虚线蓝框；点虚线切换；点 Continue 进入 Detecting Image（提交任务，不等待结果） |

## L4 PRD AC 逐条映射（regression）

| AC | 摘要 | 覆盖用例 | 期望 / 缺口 |
|---|---|---|---|
| AC-01 | 首屏 hero/默认维度 | L2-003/L2-004/L2-005 | 三页标题与默认维度正确 |
| AC-02 | 上传组件/隐私 | L2-003/L2-004/L2-005 | 文案齐全 |
| AC-03 | 正文 SEO 保持原样 | L2-001/L2-003/L2-004/L2-005 | 文案不改；维度切换原图变化见 bug candidate 02 |
| AC-04 | 维度 10 项 + 一句话描述 | L2-001 | 描述缺失→bug candidate 01 |
| AC-05 | 维度切换不改原图/主体 | L2-001 | URL/H1 不变；原图变化→bug candidate 02 |
| AC-06 | Face 双上传位 + Start | L2-005 | 结构正确 |
| AC-07 | 缩略图 + Re-upload/Delete | L2-002 | 结构正确 |
| AC-08 | 空/单图 toast | L3-002 | toast 文案精确 |
| AC-09 | No Face Found/多脸/Photo A-B tab | L3-004/L3-005 | 无人脸弹层与多人脸选择已覆盖；Face Photo A/B tab 未覆盖 |
| AC-10 | Body 三围可选输入 | L2-004/L5-001 | 可编辑 |
| AC-11 | Body 上传+Continue 出结果 | L2-004 | 结果态出现 |
| AC-12 | Ethnicity 上传自动出结果 | L2-003 | 结果态出现 |
| AC-13 | Face 双图+Start 出结果 | L2-005 | 结果态出现 |
| AC-14 | Download report 下载 JPG | L2-006 | 下载 + 问卷 |
| AC-15 | Upload another photo / Unsaved Report | L2-007 | 弹层与两按钮行为 |
| AC-16 | Try My Photo→/agent | L2-008 | 新开 /agent?pid=... |
| AC-17 | 首次下载问卷 Q1/Q2/Q3 | L2-006 | 三题选项齐全 |
| AC-18 | 匿名上传 auth wall | L3-001 | auth modal |

## L5 数据边界与等价类（default_full）

| ID | P | 测试点 | 数据 | 期望 |
|---|---|:---:|---|---|
| TC-POR-L5-001 | P1 | 三围完整 | Bust=88/Waist=70/Hips=96 | Continue 后正常出结果 |


## page_ref 与 selector 表

| 元素 | selector |
|---|---|
| 维度下拉 | `button[aria-expanded]:has-text('<Dimension>')` |
| Ethnicity 上传 | `button:has-text('Upload Image')` |
| Body 上传 / Continue | `button:has-text('Upload Photo')` / `button:has-text('Continue')` |
| Face 上传 A/B / Start | `button:has-text('Upload Photo A')` / `button:has-text('Upload Photo B')` / `button:has-text('Start Comparison')` |
| 三围输入 | `input[aria-label='Bust in cm']` 等 |
| Download report / Upload another photo / Try My Photo | `button:has-text('Download report')` / `button:has-text('Upload another photo')` / `button:has-text('Try My Photo')` |
| 报告图 | `img[alt='Your AI detection report']` |
| Unsaved Report 弹层 | `text='Unsaved Report'` / `button:has-text('Download')` / `button:has-text('Upload Without Saving')` |
| 问卷弹层 | `button:has-text('Maybe later')` / `button:has-text('Submit')` / `button[aria-label='Close']` |
| Auth 弹层 | `[data-testid='auth-dialog']` 等 |

## 依赖缺口与风险

- 图像边界（原 L5-003）：有人脸正向已由 L2-003 覆盖，无人脸/多人脸见 L3-004/L3-005；损坏的图.png 仍未验证。
- AC-09 已覆盖无人脸弹层与多人脸选择（L3-004/L3-005）；Face Photo A/B tab 仍待补充。
- bug candidate 01/02（维度描述缺失、维度切换改原图）按现状记录，不静默改写期望。
- `Submit` 空提交为 no-op，需产品确认是否先作答；脚本先按“空提交无效果”断言。
- `Try My Photo` 新开标签页为 `/agent?pid=...`，断言用 `expect_popup` + URL 正则。
- 结果生成消耗 credits，回归执行需控制生成次数。

> 本文档 confirmed 之前不得进入 test-writing。
