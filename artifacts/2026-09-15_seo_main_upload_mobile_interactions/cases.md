---
task_id: 2026-09-15_seo_main_upload_mobile_interactions
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  - artifacts/2026-09-15_seo_main_upload_mobile_interactions/sync.md
  - page_map/pokecut/seo_upload_mobile/*_v1.yaml
outputs:
  case_count: 24
  priority_breakdown:
    P0: 0
    P1: 24
next_agent: test-writing
created_at: 2026-09-16 09:32:39
dedup_at: 2026-09-16 (去重：删除 4 条与 L2 完全等价的 L6)
updated_at: 2026-09-16 09:32:39
gate_waiver: 用户已确认 sync；按前序任务节奏续接用例设计（cases_review 可豁免，由用户决定）
---

# cases.md — 24 个 SEO 页面移动端主上传按钮交互

## 需求理解

- **PRD 追溯**：无新 PRD；以「对已归档的 24 个唯一 SEO 路径，在移动端复测主上传按钮的上传后交互，方法与 PC 一致」为验收基线。
- **入口与账号**：测试服 `http://10.17.1.66:3001`；移动端 390x844（Pixel 10 模拟）；会员账号 `450832596@qq.com` / 验证码 `123456`；素材 `test_images/1K.jpg`。
- **移动端登录方式**：首页/工具页只有 `Sign up`；弹窗内填 `Email` + `Verification Code`（123456，**不需点 Send**）提交即完成登录。
- **状态机**：SEO 落地页 →（Sign up 弹窗登录）→ 主上传 → 文件选择 → 处理态 → 进入 `/create/edit?pid=`（旧画布，21 页）/ `/tools/id-photo-edit?pid=`（1 页）/ 停留原页（2 页）。
- **风险操作**：只上传和观察；不点 Enhance/Generate/Confirm，不下载、不保存、不购买、不删除。
- **移动端专属断言维度**（本次重点）：路由类型、**默认激活面板**、**默认选中的功能 tab**、画布尺寸、图片图层选中态。

## L1 页面元素 / 结构（regression）

本批无独立 L1；上传入口与移动端面板结构断言并入 L2。

## L2 交互行为 / 状态迁移（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L2-001 | P1 | /tools/hd-pic-converter 移动端上传 1K.jpg 后到达原地配置态 | `page_map/pokecut/seo_upload_mobile/tools__hd-pic-converter_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 保持 `/tools/hd-pic-converter`；上传后出现原地配置态——`Select the mode and resolution you need` 文案可见 + `Standard Mode` 选择器 + `Enhance` 按钮；上传的图片预览可见。 | `L2-001_final.png` |
| L2-002 | P1 | /tools/change-passport-to-blue-background 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__change-passport-to-blue-background_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；`Background` tab 处于选中态；**功能面板 = `Change BG`**（工具工作区面板标题匹配）+ 底部激活 tab = `Background`；画布可见（实测 canvas 尺寸 [[350, 468], [281, 376]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-002_final.png` |
| L2-003 | P1 | /tools/landscape-to-portrait-converter 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__landscape-to-portrait-converter_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `AI Image Extender`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [282, 376]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-003_final.png` |
| L2-004 | P1 | /tools/watermark-remover 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__watermark-remover_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"NO_TRIGGER"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Magic Eraser`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [367, 311]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-004_final.png` |
| L2-005 | P1 | /tools/cv-photo-editor 移动端上传 1K.jpg 后到达证件照画布 | `page_map/pokecut/seo_upload_mobile/tools__cv-photo-editor_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Create My CV Photo"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/tools/id-photo-edit?pid=<uuid>`；证件照画布可见；关键词 `Photo Size` / `United States Passport` / `1200*1200` / `2inch*2inch` 可见。 | `L2-005_final.png` |
| L2-006 | P1 | /tools/add-motion-blur-effect-to-photo 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__add-motion-blur-effect-to-photo_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；`Background` tab 处于选中态；**功能面板 = `Blur Background`**（工具工作区面板标题匹配）+ 底部激活 tab = `Background`；画布可见（实测 canvas 尺寸 [[350, 468], [233, 311]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-006_final.png` |
| L2-007 | P1 | /tools/ai-beard-remover 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__ai-beard-remover_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Magic Eraser`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [367, 311]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-007_final.png` |
| L2-008 | P1 | /ai-replace/ai-clothes-changer 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/ai-replace__ai-clothes-changer_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Clothes Changer`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [367, 376]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-008_final.png` |
| L2-009 | P1 | /tools/relight-photo 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__relight-photo_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Photo Enhancer`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-009_final.png` |
| L2-010 | P1 | /tools/photo-restoration 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__photo-restoration_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Photo Enhancer`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-010_final.png` |
| L2-011 | P1 | /tools/zoom-in-photos 移动端上传 1K.jpg 后到达放大结果态 | `page_map/pokecut/seo_upload_mobile/tools__zoom-in-photos_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 保持原 SEO 页；处理态结束（`Optimizing image details` 消失）；放大结果态可见（`Before` / `After` / `Download HD`）。 | `L2-011_final.png` |
| L2-012 | P1 | /tools/monogram-maker 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__monogram-maker_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-012_final.png` |
| L2-013 | P1 | /tools/photo-background-editor 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__photo-background-editor_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；`Background` tab 处于选中态；**功能面板 = `Change BG`**（工具工作区面板标题匹配）+ 底部激活 tab = `Background`；画布可见（实测 canvas 尺寸 [[350, 468], [281, 376]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-013_final.png` |
| L2-014 | P1 | /tools/phone-wallpaper-maker 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__phone-wallpaper-maker_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Remove Background`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [367, 311]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-014_final.png` |
| L2-015 | P1 | /tools/photo-border 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__photo-border_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-015_final.png` |
| L2-016 | P1 | /tools/silhouette-maker 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__silhouette-maker_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Remove Background`**（工具工作区面板标题匹配）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [367, 311]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-016_final.png` |
| L2-017 | P1 | /tools/add-hearts-to-photo 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__add-hearts-to-photo_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-017_final.png` |
| L2-018 | P1 | /tools/youtube-banner-maker 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__youtube-banner-maker_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 裁剪态**（画布裁剪框 + 可见 `Crop` 按钮）（已知缺陷 BUG-2026-0916-01：实测未进入裁剪态，仍停留在通用 `Trending Tools` 工具列表）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-018_final.png` |
| L2-019 | P1 | /tools/car-photo-editor 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__car-photo-editor_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；`Background` tab 处于选中态；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `Background`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-019_final.png` |
| L2-020 | P1 | /tools/add-name-and-date-on-photo 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__add-name-and-date-on-photo_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-020_final.png` |
| L2-021 | P1 | /de/tools/big-head-cutout-face-cutout 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/de__tools__big-head-cutout-face-cutout_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Bild hochladen"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `Hintergrund entfernen`**（工具工作区面板标题匹配）+ 底部激活 tab = `Tools`；画布可见（实测 canvas 尺寸 [[350, 468], [367, 311]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-021_final.png` |
| L2-022 | P1 | /tools/christmas-card-maker 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/tools__christmas-card-maker_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"clicked:Upload Image"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `Trending Tools`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-022_final.png` |
| L2-023 | P1 | /zh-tw/tools/motion-blur 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/zh-tw__tools__motion-blur_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"NO_TRIGGER"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = 不自动展开**（无工具工作区面板）+ 底部激活 tab = `背景`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-023_final.png` |
| L2-024 | P1 | /th/tools/hd-pic-converter 移动端上传 1K.jpg | `page_map/pokecut/seo_upload_mobile/th__tools__hd-pic-converter_v1.yaml: states.landing.buttons.main_upload` | 1. 移动端视口 390x844 打开页面。 2. 点 `Sign up` → 填邮箱+验证码 123456 提交登录。 3. 点击主上传入口（"NO_TRIGGER"）。 4. file chooser 选 `test_images/1K.jpg`。 5. 等待上传后稳定态。 | 等待处理态结束；最多 120s | URL 匹配 `/*/create/edit?pid=<uuid>`；底部主面板 `.mobile-primary-panel` 可见；**功能面板 = `เครื่องมือปรับภาพ`**（工具工作区面板标题匹配）+ 底部激活 tab = `เครื่องมือฟรี`；画布可见（实测 canvas 尺寸 [[350, 468]]）；图片图层默认选中（选择框/拖拽手柄可见）。 | `L2-024_final.png` |

## L3 异常 / 权限 / 兼容（default_full）

- 未纳入本轮范围：移动端未登录态、非 test_images 素材、超大文件等需单独范围与预算。

## L4 PRD AC 逐条映射（regression）

| AC | 摘要 | 覆盖用例 |
|---|---|---|
| AC-01 | 移动端上传后可进入对应画布 | L2-001 ~ L2-024 |
| AC-02 | 移动端默认激活面板可断言 | L2-001 ~ L2-024（默认面板列） |
| AC-03 | 移动端图片图层默认选中 | L2-001 ~ L2-024 |
| AC-04 | 小语种入口保留语言前缀 | L2-021、L2-023、L2-024 |

## L5 数据边界与等价类（default_full）

- 本轮统一 `1K.jpg`，不扩展图片类型/分辨率/人脸数量边界。

## L6 核心 Happy Path / E2E（smoke）— 去重后为空

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|

### L6 去重说明（2026-09-16）

原 4 条 L6 与 L2 完全等价（同页面、同链路、同断言，无参数差异、无额外覆盖点），已删除：

| 删除 | 等价保留 | page_path |
|---|---|---|
| L6-001 | L2-001 | /tools/hd-pic-converter |
| L6-002 | L2-005 | /tools/cv-photo-editor |
| L6-003 | L2-013 | /tools/photo-background-editor |
| L6-004 | L2-024 | /th/tools/hd-pic-converter |

- 用例总数 28 → **24**；P0 语义并入对应 L2 用例。
- 24 条 L2 **不可再合并**：每条对应一个独立 SEO 入口 URL（不同入口属不同覆盖点，去重规则要求保留）。

## 覆盖矩阵摘要

| 维度 | 分布 |
|---|---|
| 路由 | `/create/edit?pid=` 21 页 · `/tools/id-photo-edit?pid=` 1 页 · 停留原页 2 页 · `/agent` 0 页 |
| 默认激活面板 | `Trending Tools` 17 页 · `Background` 4 页 · 本地化 3 页（de/zh-tw/th） |
| 登录 | 24 页均通过移动端 `Sign up` 弹窗完成（21 次 login-ok + 3 次 already-logged-in） |
| 素材 | `test_images/1K.jpg` 全量统一 |
