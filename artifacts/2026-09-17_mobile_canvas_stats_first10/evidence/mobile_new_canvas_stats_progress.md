# 新画布页统计移动端补充探索进展

日期：$now  
驱动：Playwright MCP only  
移动端确认：`--device "iPhone 13"` 已生效。

## 设备确认

- viewport：`390x664`
- DPR：`3`
- `pointer: coarse = true`
- `hover: none = true`
- `li.mobile-primary-panel__tab`：存在
- `button[aria-label='Layer']`：存在
- 画布 URL：`/create/edit?pid=*`

结论：当前是移动端布局，不是之前错误的桌面窄视口。

## 已通过

| 序号 | 原文标题 | URL入口 | 移动端触发 | 实际事件 | 次数 | 结论 |
|---:|---|---|---|---|---:|---|
| 16 | 新画布增强购买出现xx_yy | `/tools/photo-enhancer` | 新免费账号登录 -> SEO 页上传 `test_images/1K.jpg` -> `/create/edit?pid=*` -> Photo Enhancer -> 直接点击 `Enhance` -> 内购弹窗 | `新画布增强购买出现en_photo-enhancer` | send=1 / debug=1 | ✅ |
| 17 | 新画布增强zz购买成功xx_yy | 同上 | 内购弹窗 -> `Get Started for $1 USD` -> Debug 跳过真实购买 | `新画布增强月SE试用购买成功en_photo-enhancer` | send=1 / debug=1 | ✅；zz=月SE试用 |

关键结论：必须用新免费账号，从 SEO 页上传进入移动画布后**直接提交任务**，才会出现内购弹窗和目标 `新画布增强购买出现en_photo-enhancer`。之前的 DEBUG 改权益/先做免费处理路径会绕过这条购买出现统计。

## 证据

- `evidence/mobile_stat16_photo_enhancer_free_direct_submit_purchase_appearance_debug.log`
- `evidence/mobile_stat16_17_photo_enhancer_free_direct_submit_purchase_success_debug.log`
- `shots/mobile_stat16_17_photo_enhancer_purchase_success.png`
- raw MCP console: `.playwright-mcp/console-2026-09-20T03-50-58-530Z.log`

## 已通过补充

| 18 | 新画布抠图购买出现xx_yy | `/tools/background-remover` | 新免费账号 -> SEO 上传 -> 移动画布 -> 直接 `Remove Background` -> 内购弹窗 | `新画布抠图购买出现en_background-remover` | send=1 / debug=1 | ✅ |
| 19 | 新画布抠图zz购买成功xx_yy | 同上 | 内购弹窗 -> `Get Started for $1 USD` -> Debug 跳过真实购买 | `新画布抠图月SE试用购买成功en_background-remover` | send=1 / debug=1 | ✅；zz=月SE试用 |

## 证据补充

- `evidence/mobile_stat18_19_background_remover_free_direct_submit_purchase_appearance_debug.log`
- `evidence/mobile_stat18_19_background_remover_free_direct_submit_purchase_success_debug.log`

## 待继续

- 18/19：`/tools/background-remover`
- 20/21：`/tools/magic-eraser-with-ai-detection`
- 22/23：`/it/ai-replace`
- 24/25：`/pt/ferramentas/expandir-imagem-ia`
- 26/27：`/ai-replace/add-smile-to-photo`
- 28/29：`/body-editor`
- 30/31：`/hair-editor/virtual-hair-color-try-on`
- 32/33：AI滤镜，URL仍待用户补充
- 34/35：`/image-to-image-ai`
- 36/37：`/ai-image-generator`
- 38/39：`/ai-background`
- 40/41：`/tools/gaussian-blur`
- 42/43：`/tools/photo-restoration`
- 44/45：`/tools/add-hearts-to-photo`
- 46/47：`/tools/background-changer`


## 第 20/21 条移动端结果（2026-09-20）

- 入口：`/tools/magic-eraser-with-ai-detection`。
- 路径：新免费账号 -> SEO 上传 `test_images/1K.jpg` -> 移动画布 -> Auto Remove -> Remove People -> `Remove` -> 内购弹窗。
- 实际事件：`移动端画布页_AI消除弹窗出现`、`AI消除auto模式处理免费credits用完触发购买界面`、`移动端画布AI消除功能点数用完触发购买`、`购买界面进入`。
- 期望事件：`新画布消除购买出现en_magic-eraser-with-ai-detection`、`新画布消除月SE试用购买成功en_magic-eraser-with-ai-detection`。
- 结论：目标 `新画布消除...` 0 次，按次数门禁记为移动端 bug_candidate；未继续触发购买成功。
- 证据：`evidence/mobile_stat20_21_magic_eraser_free_direct_submit_purchase_appearance_debug.log`。

## 第 22/23 条移动端结果（2026-09-20）

- 入口：`/it/ai-replace`。
- 路径：新免费账号 -> SEO 上传 `test_images/1K.jpg` -> `/it/create/edit?pid=*` -> AI Replace -> 绘制选区 -> 填写 `borsa` -> `Genera` -> 内购弹窗。
- 实际事件：`移动端画布AI改图功能点数用完触发购买`、`画布页改图购买出现it_ai-replace`、`购买界面进入`。
- 期望事件：`新画布改图购买出现it_ai-replace`、`新画布改图月SE试用购买成功it_ai-replace`。
- 结论：目标 `新画布改图...` 0 次，实际为 `画布页改图...`，按次数门禁记为移动端 bug_candidate。
- 证据：`evidence/mobile_stat22_23_ai_replace_free_direct_submit_purchase_appearance_debug.log`。

## 第 24/25 条移动端结果（2026-09-20）

- 入口：`/pt/ferramentas/expandir-imagem-ia`。
- 路径：新免费账号 -> SEO 上传 `test_images/1K.jpg` -> `/pt/create/edit?pid=*` -> AI Extender -> `Estenda IA` -> 内购弹窗。
- 第 24 条实际：`新画布扩图购买出现pt_expandir-imagem-ia`，send=1 / debug=1，✅。
- 第 25 条实际：`新画布扩图月SE试用购买成功pt_expandir-imagem-ia`，send=1 / debug=1，✅；符合 `zz=月SE试用`。
- 证据：`evidence/mobile_stat24_25_ai_extender_free_direct_submit_purchase_appearance_debug.log`、`evidence/mobile_stat24_25_ai_extender_free_direct_submit_purchase_success_debug.log`。

## 第 20/21 条移动端复核通过（2026-09-20）

- 入口：/tools/magic-eraser-with-ai-detection。
- 正确路径：已登录免费账号 -> SEO 首屏上传 test_images/1K.jpg -> 移动画布 -> Magic Eraser -> AI Delete -> All -> Remove -> 内购弹窗 -> Debug 跳过真实购买。
- 第 20 条实际：新画布消除购买出现en_magic-eraser-with-ai-detection，send=1 / debug=1，✅。
- 第 21 条实际：新画布消除月SE试用购买成功en_magic-eraser-with-ai-detection，send=1 / debug=1，✅。
- 关键修正：Auto Remove -> Remove People 是 auto 模式，不等于 AI Delete 的快速全选 AI 消除；必须走 AI Delete -> All -> Remove。
- 证据：evidence/mobile_stat20_magic_eraser_ai_delete_all_purchase_appearance_full_debug.log、evidence/mobile_stat20_21_magic_eraser_ai_delete_all_purchase_success_full_debug.log、shots/mobile_stat20_21_magic_eraser_ai_delete_all_purchase_success.png。

## 第 26/27、28/29、30/31、34/35、36/37 条移动端通过（2026-09-20）

| 序号 | 原文标题 | URL入口 | 触发交互 | 实际事件 | 次数 | 结论 |
|---:|---|---|---|---|---:|---|
| 26 | 新画布脸部购买出现xx_yy | `/ai-replace/add-smile-to-photo` | 首屏上传 -> AI Face Editor -> Teeth Smile -> Generate -> 购买弹窗 | `新画布脸部购买出现en_add-smile-to-photo` | send=1/debug=1 | ✅ |
| 27 | 新画布脸部zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布脸部月SE试用购买成功en_add-smile-to-photo` | send=1/debug=1 | ✅ zz=月SE试用 |
| 28 | 新画布身材购买出现xx_yy | `/body-editor` | 首屏上传 -> AI Body Editor -> Fuller Breast -> Generate -> 购买弹窗 | `新画布身材购买出现en_body-editor` | send=1/debug=1 | ✅ |
| 29 | 新画布身材zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布身材月SE试用购买成功en_body-editor` | send=1/debug=1 | ✅ |
| 30 | 新画布发型购买出现xx_yy | `/hair-editor/virtual-hair-color-try-on` | 首屏上传 -> HairStyle Try On -> Full Head Color -> Generate -> 购买弹窗 | `新画布发型购买出现en_virtual-hair-color-try-on` | send=1/debug=1 | ✅ |
| 31 | 新画布发型zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布发型月SE试用购买成功en_virtual-hair-color-try-on` | send=1/debug=1 | ✅ |
| 34 | 新画布图生图购买出现xx_yy | `/image-to-image-ai` | 首屏上传 -> AI Image -> Generate -> 购买弹窗 | `新画布图生图购买出现en_image-to-image-ai` | send=1/debug=1 | ✅ |
| 35 | 新画布图生图zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布图生图月SE试用购买成功en_image-to-image-ai` | send=1/debug=1 | ✅ |
| 36 | 新画布文生图购买出现xx_yy | `/ai-image-generator` | 首屏 Generate -> AI Image -> Generate -> 购买弹窗 | `新画布文生图购买出现en_ai-image-generator` | send=1/debug=1 | ✅ |
| 37 | 新画布文生图zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布文生图月SE试用购买成功en_ai-image-generator` | send=1/debug=1 | ✅ |


## 第 40/41、42/43、46/47 条移动端通过；38/39、44/45 不适用（2026-09-20）

| 序号 | 原文标题 | URL入口 | 触发交互 | 实际事件 | 次数 | 结论 |
|---:|---|---|---|---|---:|---|
| 40 | 新画布背景模糊购买出现xx_yy | `/tools/gaussian-blur` | 首屏上传 -> 自动 BG Blur 购买弹窗 | `新画布背景模糊购买出现en_gaussian-blur` | send=1/debug=1 | ✅ |
| 41 | 新画布背景模糊zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布背景模糊月SE试用购买成功en_gaussian-blur` | send=1/debug=1 | ✅ |
| 42 | 新画布照片修复购买出现xx_yy | `/tools/photo-restoration` | 首屏上传 -> 默认 Old Photo Enhance -> Enhance -> 购买弹窗 | `新画布照片修复购买出现en_photo-restoration` | send=1/debug=1 | ✅ |
| 43 | 新画布照片修复zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布照片修复月SE试用购买成功en_photo-restoration` | send=1/debug=1 | ✅ |
| 46 | 新画布换背购买出现xx_yy | `/tools/background-changer` | 首屏上传 -> 自动 Change BG 购买弹窗 | `新画布换背购买出现en_background-changer` | send=1/debug=1 | ✅ |
| 47 | 新画布换背zz购买成功xx_yy | 同上 | Debug 跳过真实购买 | `新画布换背月SE试用购买成功en_background-changer` | send=1/debug=1 | ✅ |

- 38/39 AI背景：用户确认移动端无该功能，不测，标记 mobile-not-applicable。
- 44/45 贴纸：用户确认移动端无该功能，不测，标记 mobile-not-applicable。

