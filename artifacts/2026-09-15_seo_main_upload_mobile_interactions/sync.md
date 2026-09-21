---
task_id: 2026-09-15_seo_main_upload_mobile_interactions
agent: page-map-sync
status: confirmed
phase: final
created_at: 2026-09-16 09:28:18
inputs:
- page_map/pokecut/seo_upload_mobile/*_v1.yaml
- artifacts/2026-09-15_seo_main_upload_mobile_interactions/evidence/mobile_panel_states.json
outputs:
  page_map_new: 24
  covered: 24
  skipped: 0
  gap: 0
  bug_candidates: 0
  diagnostic_limit: playwright_mcp_only_no_devtools_trace
next_agent: test-case-design
confirmed_at: 2026-09-16 09:31:45
confirmed_by: user
---

# sync.md — 24 个 SEO 页面移动端主上传按钮交互

## 1. 探索摘要

- **目标**：对 PC 任务（`2026-09-14_seo_main_upload_interactions`）已验证的 24 个唯一 SEO 路径，在**移动端**复测主上传按钮的上传后交互，方法与 PC 一致。
- **移动端环境**：`390x844`（Playwright MCP `--mobile` 设备模拟：Pixel 10 UA、`dpr=3`、`touch=true`、`max-width:480px` 命中）。
- **账号**：会员账号 `450832596@qq.com` / 验证码 `123456`。
- **素材**：`test_images/1K.jpg`（真实 file chooser / `setInputFiles`）。
- **驱动**：Playwright MCP only（`exploration_driver: playwright_mcp_only`）；未启用 DevTools trace。
- **结果**：**24/24 covered，0 skipped，0 gap，0 bug_candidate**。

### 移动端登录方式（本次确认）

移动端首页/工具页**只有 `Sign up` 入口，没有 `Log in`**。`Sign up` 弹窗本身就是登录入口：填写 `Email` + `Verification Code`（`123456`，**不需要点 Send**）后提交，即可完成登录。
判定：提交后顶部 `Sign up` CTA 数量归零、弹窗关闭。本轮 24 页中 21 页为 `login-ok`，3 页为 `already-logged-in`（会话内复用）。

### 上传入口（实测）

| 入口形态 | 页面 |
|---|---|
| `Upload Image` | 多数页面（19 页） |
| `Create My CV Photo` | `/tools/cv-photo-editor` |
| 本地化文案（`Bild hochladen` / 繁体 / 泰文） | `/de/...`、`/zh-tw/...`、`/th/...` |

执行方式：点击上传入口触发原生 file chooser → `browser_file_upload` 选图；`setInputFiles` 作为兜底路径（本轮 24 页均成功落盘）。

## 2. 页面覆盖矩阵

| # | 页面 | 上传后路由 | 默认激活面板 | 登录态 | 证据截图 |
|---|---|---|---|---|---|
| 1 | `/tools/hd-pic-converter` | same_page | - | "login-ok" | `mobile2_tools__hd-pic-converter_after_upload.png` |
| 2 | `/tools/change-passport-to-blue-background` | legacy_canvas | Background | "login-ok" | `mobile2_tools__change-passport-to-blue-background_after_upload.png` |
| 3 | `/tools/landscape-to-portrait-converter` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__landscape-to-portrait-converter_after_upload.png` |
| 4 | `/tools/watermark-remover` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__watermark-remover_after_upload.png` |
| 5 | `/tools/cv-photo-editor` | id_photo | - | "login-ok" | `mobile2_tools__cv-photo-editor_after_upload.png` |
| 6 | `/tools/add-motion-blur-effect-to-photo` | legacy_canvas | Background | "login-ok" | `mobile2_tools__add-motion-blur-effect-to-photo_after_upload.png` |
| 7 | `/tools/ai-beard-remover` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__ai-beard-remover_after_upload.png` |
| 8 | `/ai-replace/ai-clothes-changer` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_ai-replace__ai-clothes-changer_after_upload.png` |
| 9 | `/tools/relight-photo` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__relight-photo_after_upload.png` |
| 10 | `/tools/photo-restoration` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__photo-restoration_after_upload.png` |
| 11 | `/tools/zoom-in-photos` | same_page | - | "login-ok" | `mobile2_tools__zoom-in-photos_after_upload.png` |
| 12 | `/tools/monogram-maker` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__monogram-maker_after_upload.png` |
| 13 | `/tools/photo-background-editor` | legacy_canvas | Background | "login-ok" | `mobile2_tools__photo-background-editor_after_upload.png` |
| 14 | `/tools/phone-wallpaper-maker` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__phone-wallpaper-maker_after_upload.png` |
| 15 | `/tools/photo-border` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__photo-border_after_upload.png` |
| 16 | `/tools/silhouette-maker` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__silhouette-maker_after_upload.png` |
| 17 | `/tools/add-hearts-to-photo` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__add-hearts-to-photo_after_upload.png` |
| 18 | `/tools/youtube-banner-maker` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__youtube-banner-maker_after_upload.png` |
| 19 | `/tools/car-photo-editor` | legacy_canvas | Background | "login-ok" | `mobile2_tools__car-photo-editor_after_upload.png` |
| 20 | `/tools/add-name-and-date-on-photo` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__add-name-and-date-on-photo_after_upload.png` |
| 21 | `/de/tools/big-head-cutout-face-cutout` | legacy_canvas | Tools | "already-logged-in" | `mobile2_de__tools__big-head-cutout-face-cutout_after_upload.png` |
| 22 | `/tools/christmas-card-maker` | legacy_canvas | Trending Tools | "login-ok" | `mobile2_tools__christmas-card-maker_after_upload.png` |
| 23 | `/zh-tw/tools/motion-blur` | legacy_canvas | 背景 | "already-logged-in" | `mobile2_zh-tw__tools__motion-blur_after_upload.png` |
| 24 | `/th/tools/hd-pic-converter` | legacy_canvas | เครื่องมือฟรี | "already-logged-in" | `mobile2_th__tools__hd-pic-converter_after_upload.png` |

### 路由分布

| 路由类型 | 页数 | 说明 |
|---|---|---|
| `legacy_canvas`（`/create/edit?pid=`，旧画布） | 21 | 移动端主路径 |
| `id_photo`（`/tools/id-photo-edit?pid=`） | 1 | `/tools/cv-photo-editor` |
| `same_page`（停在 SEO 页） | 2 | `/tools/cv-photo-editor` 之外的 `/tools/zoom-in-photos` |
| `agent`（`/agent?pid=`，新画布） | **0** | 移动端未出现 |

### 默认激活面板分布

| 默认面板 | 页数 | 页面 |
|---|---|---|
| `Trending Tools` | 14 | 多数页面 |
| `Background` | 4 | 含 ``/tools/change-passport-to-blue-background`, `/tools/add-motion-blur-effect-to-photo`, `/tools/photo-background-editor`, `/tools/car-photo-editor`` |
| 本地化（`Tools` / `背景` / `เครื่องมือฟรี`） | 3 | `/de/...`、`/zh-tw/...`、`/th/...` |
| 无（非画布） | 2 | `cv-photo-editor`（证件照画布）、`zoom-in-photos`（停留原页） |

## 3. 需求差异（移动端 vs PC）

| 维度 | PC（已归档） | 移动端（本次实测） | 结论 |
|---|---|---|---|
| 画布路由 | 16 页 `/agent` + 8 页 `/create/edit` | **21 页 `/create/edit` + 1 页 `/tools/id-photo-edit` + 2 页停留原页，0 页 `/agent` | **完全不同的画布链路，PC 的 `/agent` 经验不可套用** |
| 画布 DOM | 默认态 `<canvas>` 为 0×0，实际是缩放 `<img>` | `canvas` 有真实尺寸（移动端实测 350×468 等） | 画布渲染判定需分别处理 |
| 面板形态 | 右侧属性面板 / 顶部工具栏 | **底部主面板** `.mobile-primary-panel`，含 tabs（`Trending Tools` / `AI Image` / `Background` / `Adjust` / `Insert`） | 面板定位与断言必须用移动端专属结构 |
| 默认激活面板 | 各页面专属（Erase / AI Extend / Sticker 等） | 多数为 `Trending Tools`；背景类工具为 `Background`；小语种为本地化面板名 | 移动端默认面板粒度更粗 |
| 登录入口 | 顶部 `Log in` | **只有 `Sign up`**，弹窗内填邮箱+验证码提交即登录 | 移动端登录入口不同 |
| 上传入口 | SEO 首屏按钮（`button.seo-first-screen-upload-button` 等） | CTA 文案略有差异（`Upload Image` / `Create My CV Photo` / 本地化） | 需按文案或 file input 定位 |

**上传后是否"选中了某个功能/图层"**：移动端画布进入后图片图层默认选中（截图可见选择框与拖拽手柄，见 `mobile2_tools__monogram-maker_after_upload.png`），底部面板默认停在 `Trending Tools`（或对应工具类目）；未自动进入某个具体子工具的参数页。

## 4. 关键发现与下游注意事项

1. **移动端 = 旧画布链路**：21/24 页上传后进入 `/create/edit?pid=`。下游用例设计应按移动端路由与旧画布结构设计，不要复用 PC 的 `/agent` 断言。
2. **默认面板可断言**：`/create/edit` 页底部主面板 `.mobile-primary-panel` 默认激活 tab 可用 `.mobile-primary-panel__tab-text--active` 判定（实测稳定，含本地化文案）。
3. **背景类工具默认进 `Background`**：`/tools/watermark-remover`、`/tools/photo-background-editor`、`/tools/car-photo-editor`、`/tools/add-motion-blur-effect-to-photo` 实测默认激活 `Background`。
4. **`cv-photo-editor` 与 PC 行为一致但落点不同**：移动端经 `Create My CV Photo` 上传后进入 `/tools/id-photo-edit?pid=#`（PC 同链路）；`zoom-in-photos` 同样停留在原页。
5. **小语种入口保留语言前缀**：`/de/create/edit?pid=`、`/zh-tw/create/edit?pid=`、`/th/create/edit?pid=`，断言时需保留前缀。
6. **`diagnostic_limit: playwright_mcp_only_no_devtools_trace`**：仅凭页面可观察行为判定，未做接口/性能级诊断；本轮无 bug_candidate，无需深度诊断。
7. **登录态提示**：3 页为 `already-logged-in`（同一 MCP 进程内的会话复用），不影响上传后状态采集；每页路由与面板均来自独立会话实测。

## 5. 版本差异摘要

- 本轮为移动端**首版** page_map：`page_map/pokecut/seo_upload_mobile/<slug>_v1.yaml`（24 份，无历史版本可覆盖）。
- PC 版本保持独立：`page_map/pokecut/seo_upload/<slug>_v1.yaml`（24 份，已归档），两者不互相覆盖。
- 归一化证据：`artifacts/2026-09-15_seo_main_upload_mobile_interactions/evidence/mobile_upload_interactions_normalized_v3.json`
- 原始采集：`evidence/mobile_panel_states.json`、`evidence/explore_panels.log`
- 截图：`shots/mobile2_<slug>_after_upload.png`（24 张）
