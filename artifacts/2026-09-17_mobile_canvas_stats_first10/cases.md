---
task_id: 2026-09-17_mobile_canvas_stats_first10
agent: test-case-design
phase: final_after_sync
status: confirmed
revision: 3
revision_reason: 用户要求 Allure 只分 PC端 / 移动端两个顶层维度；仅保留正常路径统计用例；同一链路事件合并
inputs:
  sync: artifacts/2026-09-17_mobile_canvas_stats_first10/sync.md
  page_map: page_map/pokecut/mobile_canvas_v9.yaml
  requirement_doc: D:/Test/my_project/testcases/v3.2_testcases_source/04_版本统计优化.md
outputs:
  case_count: 40
  priority_breakdown:
    P0: 32
    P1: 6
    P2: 2
  dimension_breakdown:
    PC端: 19
    移动端: 21
  allure_grouping:
    epic:
      - PC端
      - 移动端
    feature:
      PC端: [注册登录, 无限画布, 新画布]
      移动端: [注册登录, 画布页, 新画布]
next_agent: test-writing
created_at: 2026-09-20 15:21:33
updated_at: 2026-09-20 16:41:22
---

# Pokecut 画布统计优化正常路径用例矩阵（PC端 / 移动端两大类）

## Allure 顶层分组约定

Allure 报告中**只出现两个顶层大类**，不使用其他 epic：

| 顶层大类（`allure.epic`） | 二级分组（`allure.feature`） | 用例前缀 |
|---|---|---|
| `PC端` | `注册登录` | `P-INF-01` |
| `PC端` | `无限画布` | `P-INF-02`, `P-INF-03` |
| `PC端` | `新画布` | `P-NEW-01` ~ `P-NEW-16` |
| `移动端` | `注册登录` | `M-CORE-01`, `M-CORE-02` |
| `移动端` | `画布页` | `M-CORE-03` ~ `M-CORE-07` |
| `移动端` | `新画布` | `M-NEW-01` ~ `M-NEW-14` |

约束：

- `epic` 只允许取值 `PC端` / `移动端`；`feature` 只允许取上表二级分组，不得新增第三层大类。
- `story` 使用对应用例 ID，`title` 使用本文件「测试点」列。
- 跨端不单列分类；同一功能的 PC / 移动端用例各自归入所属大类。

---

## 需求理解

- 需求来源：`04_版本统计优化.md`，共 47 条统计定义。
- 本轮范围：只保留**正常路径统计测例**；页面结构类、异常/权限/兼容类、数据边界与等价类用例全部移除。
- 去重规则：同一链路产生的多个统计项合并为一条用例；多功能/多内购只抽测 1~2 个功能和 1~2 个内购项。
- 统计验收：单次目标动作内，目标 `sendGaEvent <事件名>` 出现 1 次，且 `debug 统计：<事件名>` 出现 1 次；0 次漏报、>=2 次多报均失败。
- PC 维度：无限画布 `/create -> Start from a Photo -> /agent?pid=*`；新画布从 SEO 功能介绍页首屏进入。
- 移动端维度：iPhone 13 真实移动模拟（pointer coarse=true、hover none=true），SEO 页上传后进入 `/create/edit?pid=*`。
- 账号维度：注册统计用匿名态；购买出现用免费 0 credits 账号；购买成功仅用 Debug“跳过真实购买（查看统计项用）”。
- 素材约束：所有上传使用 `test_images/1K.jpg`。
- 内购抽测：PC 端统一抽测 `年ultra`；移动端统一抽测 `月SE试用`。
- 移动端不适用：移动端无 AI背景、贴纸功能，38/39、44/45 移动端不建用例。

---

# 一、PC端

## PC端 - 注册登录（`epic=PC端`, `feature=注册登录`）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| P-INF-01 | P0 | PC 无限画布增强点数用完触发注册与注册成功 | `pc_canvas_anonymous_enhance_register`, `pc_canvas_register_success` | 1. 匿名 Credits:0 进入 `/agent?pid=*`<br>2. Enhance -> Ultra HD Mode -> Enhance 触发注册弹窗<br>3. 填随机唯一邮箱 + 验证码 `123456` -> Sign up | 注册弹窗出现后完成注册 | 期望 `无限画布页画质增强ultra功能点数用完触发注册` 与 `无限画布页画质增强ultra功能点数用完触发注册成功` 各 send=1 / debug=1；当前实际为通用注册事件，结论 `blocked_by_bug` | `pc_login_01_register_bug.png` |

## PC端 - 无限画布（`epic=PC端`, `feature=无限画布`）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| P-INF-02 | P0 | PC 无限画布点数用完触发购买成功 | `pc_canvas_purchase_debug_skip_success` | 1. 免费 0 credits 进入 Enhance 购买面板<br>2. 选择 Yearly Ultra<br>3. 打开 DEBUG 勾选跳过真实购买并点击 `Debug: 跳过真实购买` | 购买成功回调出现 | `无限画布页点数用完触发购买年ultra成功` send=1 / debug=1 | `pc_inf_02_purchase_success.png` |
| P-INF-03 | P0 | PC 无限画布结果图下载保存 | `pc_canvas_stat15_result_image_download_recheck_20260920` | 1. `/create -> Start from a Photo -> test_images/1K.jpg -> /agent?pid=*`<br>2. Enhance Standard Mode 生成成功<br>3. 选中 Enhanced 结果图层后点击下载 | 下载触发 | `无限画布页画质增强ultra功能图片下载保存` send=1 / debug=1；不得下载原图 | `pc_inf_03_result_download.png` |

## PC端 - 新画布（`epic=PC端`, `feature=新画布`）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| P-NEW-01 | P0 | PC 新画布增强购买出现与成功 | `pc_canvas_stats_16_25_correct_landing` | 1. `/tools/photo-enhancer` 首屏上传 `test_images/1K.jpg` 进入 PC 画布<br>2. 触发 Enhance 购买弹窗<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布增强购买出现en_photo-enhancer` 与 `新画布增强年ultra购买成功en_photo-enhancer` 均 send=1 / debug=1 | `pc_new_01_enhancer.png` |
| P-NEW-02 | P0 | PC 新画布抠图购买出现与成功 | `pc_canvas_stats_16_25_correct_landing` | 1. `/tools/background-remover` 首屏上传<br>2. 触发 Remove Background 购买弹窗<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布抠图购买出现en_background-remover` 与 `新画布抠图年ultra购买成功en_background-remover` 均 send=1 / debug=1 | `pc_new_02_remove_bg.png` |
| P-NEW-03 | P0 | PC 新画布消除购买出现与成功 | `pc_canvas_stats_16_25_correct_landing` | 1. `/tools/magic-eraser-with-ai-detection` 首屏上传<br>2. AI Delete -> All -> Remove 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布消除购买出现en_magic-eraser-with-ai-detection` 与 `新画布消除年ultra购买成功en_magic-eraser-with-ai-detection` 均 send=1 / debug=1 | `pc_new_03_magic_eraser.png` |
| P-NEW-04 | P0 | PC 新画布改图购买出现与成功 | `pc_canvas_stats_16_25_correct_landing` | 1. `/it/ai-replace` 首屏上传<br>2. 选区 + prompt + Genera 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布改图购买出现it_ai-replace` 与 `新画布改图年ultra购买成功it_ai-replace` 均 send=1 / debug=1 | `pc_new_04_ai_replace.png` |
| P-NEW-05 | P0 | PC 新画布扩图购买出现与成功 | `pc_canvas_stats_16_25_correct_landing` | 1. `/pt/ferramentas/expandir-imagem-ia` 首屏上传<br>2. Estenda IA 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布扩图购买出现pt_expandir-imagem-ia` 与 `新画布扩图年ultra购买成功pt_expandir-imagem-ia` 均 send=1 / debug=1 | `pc_new_05_extend.png` |
| P-NEW-06 | P0 | PC 新画布脸部购买出现与成功 | `pc_canvas_stats_26_31_38_41_correct_landing` | 1. `/ai-replace/add-smile-to-photo` 实际跳转 `/face-editor/add-smile-to-photo` 并上传<br>2. Portrait Editor -> Face -> Remove Acne -> Generate<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布脸部购买出现en_add-smile-to-photo` 与 `新画布脸部年ultra购买成功en_add-smile-to-photo` 均 send=1 / debug=1 | `pc_new_06_face.png` |
| P-NEW-07 | P0 | PC 新画布身材购买出现与成功 | `pc_canvas_stats_26_31_38_41_correct_landing` | 1. `/body-editor` 首屏上传<br>2. Body -> Natural Breast -> Generate<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布身材购买出现en_body-editor` 与 `新画布身材年ultra购买成功en_body-editor` 均 send=1 / debug=1 | `pc_new_07_body.png` |
| P-NEW-08 | P0 | PC 新画布发型购买出现与成功 | `pc_canvas_stats_26_31_38_41_correct_landing` | 1. `/hair-editor/virtual-hair-color-try-on` 首屏上传<br>2. Hair -> Blonde -> Generate<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布发型购买出现en_virtual-hair-color-try-on` 与 `新画布发型年ultra购买成功en_virtual-hair-color-try-on` 均 send=1 / debug=1 | `pc_new_08_hair.png` |
| P-NEW-09 | P2 | PC 新画布 AI滤镜购买出现与成功 | `sync.md#10 skipped` | 1. 等待提供 AI滤镜 SEO URL<br>2. 首屏上传并触发 AI Filter 购买<br>3. Debug 跳过真实购买 | 不可执行 | URL 未提供，标 `skipped_dependency`；不得用其他滤镜事件替代 | `pc_new_09_skipped.png` |
| P-NEW-10 | P0 | PC 新画布图生图购买出现与成功 | `pc_canvas_stats_34_37_42_47_correct_landing_20260920` | 1. `/image-to-image-ai` 首屏上传 `test_images/1K.jpg`<br>2. Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布图生图购买出现en_image-to-image-ai` 与 `新画布图生图年ultra购买成功en_image-to-image-ai` 均 send=1 / debug=1 | `pc_new_10_image2image.png` |
| P-NEW-11 | P0 | PC 新画布文生图购买出现与成功 | `pc_canvas_stats_34_37_42_47_correct_landing_20260920` | 1. `/ai-image-generator` 使用默认提示词<br>2. Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布文生图购买出现en_ai-image-generator` 与 `新画布文生图年ultra购买成功en_ai-image-generator` 均 send=1 / debug=1 | `pc_new_11_text2image.png` |
| P-NEW-12 | P1 | PC 新画布 AI背景购买出现与成功 | `pc_canvas_stats_26_31_38_41_correct_landing` | 1. `/ai-background` 首屏上传<br>2. 自动触发 AI Background 购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布AI背景购买出现en_ai-background` 与 `新画布AI背景年ultra购买成功en_ai-background` 均 send=1 / debug=1 | `pc_new_12_ai_background.png` |
| P-NEW-13 | P0 | PC 新画布背景模糊购买出现与成功 | `pc_canvas_stats_26_31_38_41_correct_landing` | 1. `/tools/gaussian-blur` 首屏上传<br>2. 自动触发 BG Blur 购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布背景模糊购买出现en_gaussian-blur` 与 `新画布背景模糊年ultra购买成功en_gaussian-blur` 均 send=1 / debug=1 | `pc_new_13_blur.png` |
| P-NEW-14 | P0 | PC 新画布照片修复购买出现与成功 | `pc_canvas_stats_34_37_42_47_correct_landing_20260920` | 1. `/tools/photo-restoration` 首屏上传<br>2. 保持默认 Old Photo Mode -> Enhance<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布照片修复购买出现en_photo-restoration` 与 `新画布照片修复年ultra购买成功en_photo-restoration` 均 send=1 / debug=1 | `pc_new_14_photo_restoration.png` |
| P-NEW-15 | P1 | PC 新画布贴纸购买出现与成功 | `pc_canvas_stats_34_37_42_47_correct_landing_20260920` | 1. `/tools/add-hearts-to-photo` 首屏上传<br>2. Valentine 2 -> 第二个 VIP 贴纸 -> 框选全部图层 -> Download VIP<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布贴纸购买出现en_add-hearts-to-photo` 与 `新画布贴纸年ultra购买成功en_add-hearts-to-photo` 均 send=1 / debug=1 | `pc_new_15_sticker.png` |
| P-NEW-16 | P0 | PC 新画布换背购买出现与成功 | `pc_canvas_stats_34_37_42_47_correct_landing_20260920` | 1. `/tools/background-changer` 首屏上传<br>2. 自动触发 Change BG 购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布换背购买出现en_background-changer` 与 `新画布换背年ultra购买成功en_background-changer` 均 send=1 / debug=1 | `pc_new_16_background_changer.png` |

---

# 二、移动端

## 移动端 - 注册登录（`epic=移动端`, `feature=注册登录`）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| M-CORE-01 | P0 | 移动端画布点数用完触发注册与注册成功 | `stats_first10_20260917.verified_states.mobile_canvas_anonymous_credits_empty_register` | 1. 匿名 0 credits 从首页进入移动画布<br>2. 打开 Photo Enhancer 并点击 `Enhance`<br>3. 注册弹窗填随机唯一邮箱 + 验证码 `123456` -> Sign up | 注册弹窗出现后转为登录态 | `移动端画布点数用完触发注册` 与 `移动端画布点数用完触发注册成功` 各 send=1 / debug=1 | `mobile_login_01_register_pair.png` |
| M-CORE-02 | P1 | 移动端 xx 功能点数用完触发注册与注册成功 | `stats_first10_20260917.verified_states.mobile_canvas_anonymous_credits_empty_register` | 1. 匿名 0 credits 进入移动画布<br>2. 抽测画质增强ultra、AI扩图触发注册<br>3. 注册成功后抽测画质增强ultra、AI扩图注册成功 | 注册弹窗稳定 | `移动端画布画质增强ultra功能点数用完触发注册`、`移动端画布AI扩图功能点数用完触发注册` 及对应注册成功事件均 send=1 / debug=1 | `mobile_login_02_feature_register.png` |

## 移动端 - 画布页（`epic=移动端`, `feature=画布页`）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| M-CORE-03 | P0 | 移动端点数用完触发购买与 xx 功能购买 | `stats_first10_20260917.verified_states.mobile_canvas_free_credits_empty_purchase` | 1. 免费 0 credits 进入移动画布<br>2. 抽测 Photo Enhancer、AI Image Extender 主处理按钮<br>3. 触发购买弹窗 | 购买弹窗出现 | `移动端画布点数用完触发购买` 与对应 xx 功能购买事件均 send=1 / debug=1 | `mobile_canvas_03_purchase_appearance.png` |
| M-CORE-04 | P0 | 移动端 xx 功能与通用购买成功 | `stats_first10_20260917.verified_states.mobile_canvas_debug_skip_purchase_success` | 1. 承接 M-CORE-03 购买弹窗<br>2. 打开 DEBUG 勾选“跳过真实购买（查看统计项用）”<br>3. 支付面板点击 `Debug: 跳过真实购买` | 购买成功回调出现 | `移动端画布AI扩图功能点数用完触发购买年ultra成功` 与 `移动端画布点数用完触发购买年ultra成功` 均 send=1 / debug=1 | `mobile_canvas_04_purchase_success.png` |
| M-CORE-05 | P1 | 移动端画布页 xx 弹窗出现 | `stats_first10_20260917.verified_states.mobile_canvas_free_credits_empty_purchase` | 1. 进入移动画布<br>2. 抽测画质增强、AI消除并打开功能面板 | 功能面板出现 | `移动端画布页_画质增强弹窗出现`、`移动端画布页_AI消除弹窗出现` 均 send=1 / debug=1 | `mobile_canvas_05_feature_modal.png` |
| M-CORE-06 | P1 | 移动端画布页 xx 弹窗确认 | `stats_first10_20260917.verified_states.mobile_canvas_adjust_filter_confirm`, `mobile_canvas_background_remover_confirm` | 1. Adjust -> Filter -> Confirm<br>2. Background -> Background Remover -> Remove Background -> Confirm | 确认完成、结果生效 | `移动端画布页_调节弹窗确认` 与 `移动端画布页_背景移除通用弹窗确认` 均 send=1 / debug=1 | `mobile_canvas_06_modal_confirm.png` |
| M-CORE-07 | P1 | 移动端画布页画质增强结果弹窗下载 | `stat11_mobile_enhance_popup_download_recheck_20260920` | 1. 登录态账号从首页进入移动画布并上传 `test_images/1K.jpg`（会员非必要条件）<br>2. Photo Enhancer -> Enhance 提交任务<br>3. 结果生成后点击功能弹窗底部下载按钮 | 下载触发 | `移动端画布页_画质增强ultra弹窗下载` send=1 / debug=1；同时记录 `移动端结果弹窗确认下载`、`下载成功` | `mobile_canvas_07_modal_download.png` |

## 移动端 - 新画布（`epic=移动端`, `feature=新画布`）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| M-NEW-01 | P0 | 移动端新画布增强购买出现与成功 | `states.mobile_canvas_default` | 1. 免费账号访问 `/tools/photo-enhancer` 并上传 `test_images/1K.jpg`<br>2. 进入 `/create/edit?pid=*` 直接 Enhance 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布增强购买出现en_photo-enhancer` 与 `新画布增强月SE试用购买成功en_photo-enhancer` 均 send=1 / debug=1 | `mobile_new_01_enhancer.png` |
| M-NEW-02 | P0 | 移动端新画布抠图购买出现与成功 | `states.mobile_canvas_default` | 1. `/tools/background-remover` 上传<br>2. 直接 Remove Background 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布抠图购买出现en_background-remover` 与 `新画布抠图月SE试用购买成功en_background-remover` 均 send=1 / debug=1 | `mobile_new_02_remove_bg.png` |
| M-NEW-03 | P0 | 移动端新画布消除购买出现与成功 | `states.mobile_canvas_default` | 1. `/tools/magic-eraser-with-ai-detection` 上传<br>2. Magic Eraser -> AI Delete -> All -> Remove<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布消除购买出现en_magic-eraser-with-ai-detection` 与 `新画布消除月SE试用购买成功en_magic-eraser-with-ai-detection` 均 send=1 / debug=1 | `mobile_new_03_magic_eraser.png` |
| M-NEW-04 | P0 | 移动端新画布改图购买出现与成功 | `states.mobile_canvas_default` | 1. `/it/ai-replace` 上传<br>2. 选区 + prompt + Genera 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | 期望 `新画布改图购买出现it_ai-replace` 与 `新画布改图月SE试用购买成功it_ai-replace`；当前实际 `画布页改图购买出现it_ai-replace`，结论 `blocked_by_bug` | `mobile_new_04_ai_replace_bug.png` |
| M-NEW-05 | P0 | 移动端新画布扩图购买出现与成功 | `states.mobile_canvas_default` | 1. `/pt/ferramentas/expandir-imagem-ia` 上传<br>2. Estenda IA 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布扩图购买出现pt_expandir-imagem-ia` 与 `新画布扩图月SE试用购买成功pt_expandir-imagem-ia` 均 send=1 / debug=1 | `mobile_new_05_extend.png` |
| M-NEW-06 | P0 | 移动端新画布脸部购买出现与成功 | `states.mobile_canvas_default` | 1. `/ai-replace/add-smile-to-photo` 实际落地 `/face-editor/add-smile-to-photo` 并上传<br>2. Teeth Smile -> Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布脸部购买出现en_add-smile-to-photo` 与 `新画布脸部月SE试用购买成功en_add-smile-to-photo` 均 send=1 / debug=1 | `mobile_new_06_face.png` |
| M-NEW-07 | P0 | 移动端新画布身材购买出现与成功 | `states.mobile_canvas_default` | 1. `/body-editor` 上传<br>2. Fuller Breast -> Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布身材购买出现en_body-editor` 与 `新画布身材月SE试用购买成功en_body-editor` 均 send=1 / debug=1 | `mobile_new_07_body.png` |
| M-NEW-08 | P0 | 移动端新画布发型购买出现与成功 | `states.mobile_canvas_default` | 1. `/hair-editor/virtual-hair-color-try-on` 上传<br>2. Full Head Color -> Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布发型购买出现en_virtual-hair-color-try-on` 与 `新画布发型月SE试用购买成功en_virtual-hair-color-try-on` 均 send=1 / debug=1 | `mobile_new_08_hair.png` |
| M-NEW-09 | P2 | 移动端新画布 AI滤镜购买出现与成功 | `sync.md#10 skipped` | 1. 等待提供 AI滤镜 SEO URL<br>2. 上传并触发 AI Filter 购买<br>3. Debug 跳过真实购买 | 不可执行 | URL 未提供，标 `skipped_dependency` | `mobile_new_09_skipped.png` |
| M-NEW-10 | P0 | 移动端新画布图生图购买出现与成功 | `states.mobile_canvas_default` | 1. `/image-to-image-ai` 上传<br>2. AI Image Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布图生图购买出现en_image-to-image-ai` 与 `新画布图生图月SE试用购买成功en_image-to-image-ai` 均 send=1 / debug=1 | `mobile_new_10_image2image.png` |
| M-NEW-11 | P0 | 移动端新画布文生图购买出现与成功 | `states.mobile_canvas_default` | 1. `/ai-image-generator` 首屏 Generate 进入移动画布<br>2. AI Image Generate 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布文生图购买出现en_ai-image-generator` 与 `新画布文生图月SE试用购买成功en_ai-image-generator` 均 send=1 / debug=1 | `mobile_new_11_text2image.png` |
| M-NEW-12 | P0 | 移动端新画布背景模糊购买出现与成功 | `states.mobile_canvas_default` | 1. `/tools/gaussian-blur` 上传<br>2. 自动触发 BG Blur 购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布背景模糊购买出现en_gaussian-blur` 与 `新画布背景模糊月SE试用购买成功en_gaussian-blur` 均 send=1 / debug=1 | `mobile_new_12_blur.png` |
| M-NEW-13 | P0 | 移动端新画布照片修复购买出现与成功 | `states.mobile_canvas_default` | 1. `/tools/photo-restoration` 上传<br>2. 保持默认 Old Photo Enhance -> Enhance 触发购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布照片修复购买出现en_photo-restoration` 与 `新画布照片修复月SE试用购买成功en_photo-restoration` 均 send=1 / debug=1 | `mobile_new_13_photo_restoration.png` |
| M-NEW-14 | P0 | 移动端新画布换背购买出现与成功 | `states.mobile_canvas_default` | 1. `/tools/background-changer` 上传<br>2. 自动触发 Change BG 购买<br>3. Debug 跳过真实购买 | 购买弹窗与成功回调 | `新画布换背购买出现en_background-changer` 与 `新画布换背月SE试用购买成功en_background-changer` 均 send=1 / debug=1 | `mobile_new_14_background_changer.png` |

---

## 缺口与阻塞用例汇总
- 代码设计规则：以下用例的断言必须使用「期望事件」；探索记录中的实际错误事件只用于说明缺口，不得写入测试断言。
- 第 11 条用户补充口径：不要求会员账号，只要功能弹窗可正常提交任务并生成结果，点击结果弹窗底部下载即可触发统计。

| 序号 | 维度 | 统计标题 | 用例 ID | 期望事件 | 实际观察 | 类型 | 结论 |
|---:|---|---|---|---|---|---|---|
| 11 | 移动端 | 移动端画布页_xx弹窗下载 | M-CORE-07 | `移动端画布页_画质增强ultra弹窗下载` | `移动端画布页_画质增强ultra弹窗下载` | 能正常提交任务并生成结果即可 | `covered` |
| 12 | PC端 | 无限画布页xx功能点数用完触发注册 | P-INF-01 | `无限画布页画质增强ultra功能点数用完触发注册` | `注册弹窗_出现` | 事件名未符合功能级命名 | `blocked_by_bug` |
| 13 | PC端 | 无限画布页xx功能点数用完触发注册成功 | P-INF-01 | `无限画布页画质增强ultra功能点数用完触发注册成功` | `注册弹窗_注册成功`、`登录成功_邮箱登录方式` | 事件名未符合功能级命名 | `blocked_by_bug` |
| 22 | 移动端 | 新画布改图购买出现xx_yy | M-NEW-04 | `新画布改图购买出现it_ai-replace` | `画布页改图购买出现it_ai-replace` | 缺 `新画布` 前缀 | `blocked_by_bug` |
| 23 | 移动端 | 新画布改图zz购买成功xx_yy | M-NEW-04 | `新画布改图月SE试用购买成功it_ai-replace` | 未观察到目标事件（0 次） | 缺 `新画布` 前缀 | `blocked_by_bug` |
| 32 | PC端 / 移动端 | 新画布AI滤镜购买出现xx_yy | P-NEW-09 / M-NEW-09 | `新画布AI滤镜购买出现xx_yy` | 未执行 | 入口 URL 缺失 | `skipped_dependency` |
| 33 | PC端 / 移动端 | 新画布AI滤镜zz购买成功xx_yy | P-NEW-09 / M-NEW-09 | `新画布AI滤镜zz购买成功xx_yy` | 未执行 | 入口 URL 缺失 | `skipped_dependency` |
| 38 | 移动端 | 新画布AI背景购买出现xx_yy | —（不建用例） | `新画布AI背景购买出现xx_yy` | 无对应功能 | 移动端无该功能 | `mobile-not-applicable` |
| 39 | 移动端 | 新画布AI背景zz购买成功xx_yy | —（不建用例） | `新画布AI背景zz购买成功xx_yy` | 无对应功能 | 移动端无该功能 | `mobile-not-applicable` |
| 44 | 移动端 | 新画布贴纸购买出现xx_yy | —（不建用例） | `新画布贴纸购买出现xx_yy` | 无对应功能 | 移动端无该功能 | `mobile-not-applicable` |
| 45 | 移动端 | 新画布贴纸zz购买成功xx_yy | —（不建用例） | `新画布贴纸zz购买成功xx_yy` | 无对应功能 | 移动端无该功能 | `mobile-not-applicable` |

### 依据引用

| 结论 | 依据 |
|---|---|
| 11 `covered` | `evidence/mobile_stat11_enhance_popup_download_after_full_debug.log`；`evidence/mobile_stat11_enhance_popup_download_recheck_summary.md` |
| 12 `blocked_by_bug` | `evidence/console_stat12_pc_enhance_ultra_register_debug.log` |
| 13 `blocked_by_bug` | `evidence/console_stat13_pc_enhance_register_success_debug.log` |
| 22 `blocked_by_bug` | `evidence/mobile_stat22_23_ai_replace_free_direct_submit_purchase_appearance_debug.log` |
| 23 `blocked_by_bug` | 同上；目标事件计数 0 |
| 32/33 `skipped_dependency` | `sync.md#10 skipped`；用户标记 URL 跳过 |
| 38/39、44/45 `mobile-not-applicable` | `evidence/mobile_stat38_39_44_45_not_applicable.md`（用户确认移动端无 AI背景 / 贴纸功能） |

---
## 统计项 → 顶层分组对照（47 条 AC）

| AC | 摘要 | PC端覆盖用例 | 移动端覆盖用例 | 期望/缺口 |
|---|---|---|---|---|
| AC-001 | 移动端画布点数用完触发注册 | — | M-CORE-01 | covered |
| AC-002 | 移动端画布点数用完触发注册成功 | — | M-CORE-01 | covered |
| AC-003 | 移动端画布xx功能点数用完触发注册 | — | M-CORE-02 | covered（抽测画质增强ultra、AI扩图） |
| AC-004 | 移动端画布xx功能点数用完触发注册成功 | — | M-CORE-02 | covered（抽测画质增强ultra、AI扩图） |
| AC-005 | 移动端画布点数用完触发购买 | — | M-CORE-03 | covered |
| AC-006 | 移动端画布xx功能点数用完触发购买 | — | M-CORE-03 | covered（抽测 Photo Enhancer、AI Image Extender） |
| AC-007 | 移动端画布xx功能点数用完触发购买yy成功 | — | M-CORE-04 | covered（yy=年ultra） |
| AC-008 | 移动端画布点数用完触发购买yy成功 | — | M-CORE-04 | covered（yy=年ultra） |
| AC-009 | 移动端画布页_xx弹窗出现 | — | M-CORE-05 | covered |
| AC-010 | 移动端画布页_xx弹窗确认 | — | M-CORE-06 | covered |
| AC-011 | 移动端画布页_xx弹窗下载 | — | M-CORE-07 | covered（xx=画质增强ultra） |
| AC-012 | 无限画布页xx功能点数用完触发注册 | P-INF-01 | — | blocked_by_bug（实际为通用注册弹窗事件） |
| AC-013 | 无限画布页xx功能点数用完触发注册成功 | P-INF-01 | — | blocked_by_bug（实际为通用注册成功事件） |
| AC-014 | 无限画布页xx功能点数用完触发购买yy成功 | P-INF-02 | — | covered（yy=年ultra） |
| AC-015 | 无限画布页xx功能图片下载保存 | P-INF-03 | — | covered（必须下载结果图） |
| AC-016 | 新画布增强购买出现xx_yy | P-NEW-01 | M-NEW-01 | PC covered；mobile covered |
| AC-017 | 新画布增强zz购买成功xx_yy | P-NEW-01 | M-NEW-01 | PC covered（年ultra）；mobile covered（月SE试用） |
| AC-018 | 新画布抠图购买出现xx_yy | P-NEW-02 | M-NEW-02 | PC covered；mobile covered |
| AC-019 | 新画布抠图zz购买成功xx_yy | P-NEW-02 | M-NEW-02 | PC covered；mobile covered |
| AC-020 | 新画布消除购买出现xx_yy | P-NEW-03 | M-NEW-03 | PC covered；mobile covered |
| AC-021 | 新画布消除zz购买成功xx_yy | P-NEW-03 | M-NEW-03 | PC covered；mobile covered |
| AC-022 | 新画布改图购买出现xx_yy | P-NEW-04 | M-NEW-04 | PC covered；mobile blocked_by_bug（缺新画布前缀） |
| AC-023 | 新画布改图zz购买成功xx_yy | P-NEW-04 | M-NEW-04 | PC covered；mobile blocked_by_bug |
| AC-024 | 新画布扩图购买出现xx_yy | P-NEW-05 | M-NEW-05 | PC covered；mobile covered |
| AC-025 | 新画布扩图zz购买成功xx_yy | P-NEW-05 | M-NEW-05 | PC covered；mobile covered |
| AC-026 | 新画布脸部购买出现xx_yy | P-NEW-06 | M-NEW-06 | PC covered；mobile covered |
| AC-027 | 新画布脸部zz购买成功xx_yy | P-NEW-06 | M-NEW-06 | PC covered；mobile covered |
| AC-028 | 新画布身材购买出现xx_yy | P-NEW-07 | M-NEW-07 | PC covered；mobile covered |
| AC-029 | 新画布身材zz购买成功xx_yy | P-NEW-07 | M-NEW-07 | PC covered；mobile covered |
| AC-030 | 新画布发型购买出现xx_yy | P-NEW-08 | M-NEW-08 | PC covered；mobile covered |
| AC-031 | 新画布发型zz购买成功xx_yy | P-NEW-08 | M-NEW-08 | PC covered；mobile covered |
| AC-032 | 新画布AI滤镜购买出现xx_yy | P-NEW-09 | M-NEW-09 | skipped_dependency（URL 未提供） |
| AC-033 | 新画布AI滤镜zz购买成功xx_yy | P-NEW-09 | M-NEW-09 | skipped_dependency（URL 未提供） |
| AC-034 | 新画布图生图购买出现xx_yy | P-NEW-10 | M-NEW-10 | PC covered；mobile covered |
| AC-035 | 新画布图生图zz购买成功xx_yy | P-NEW-10 | M-NEW-10 | PC covered；mobile covered |
| AC-036 | 新画布文生图购买出现xx_yy | P-NEW-11 | M-NEW-11 | PC covered；mobile covered |
| AC-037 | 新画布文生图zz购买成功xx_yy | P-NEW-11 | M-NEW-11 | PC covered；mobile covered |
| AC-038 | 新画布AI背景购买出现xx_yy | P-NEW-12 | — | PC covered；mobile-not-applicable（移动端无该功能） |
| AC-039 | 新画布AI背景zz购买成功xx_yy | P-NEW-12 | — | PC covered；mobile-not-applicable |
| AC-040 | 新画布背景模糊购买出现xx_yy | P-NEW-13 | M-NEW-12 | PC covered；mobile covered |
| AC-041 | 新画布背景模糊zz购买成功xx_yy | P-NEW-13 | M-NEW-12 | PC covered；mobile covered |
| AC-042 | 新画布照片修复购买出现xx_yy | P-NEW-14 | M-NEW-13 | PC covered；mobile covered |
| AC-043 | 新画布照片修复zz购买成功xx_yy | P-NEW-14 | M-NEW-13 | PC covered；mobile covered |
| AC-044 | 新画布贴纸购买出现xx_yy | P-NEW-15 | — | PC covered；mobile-not-applicable（移动端无该功能） |
| AC-045 | 新画布贴纸zz购买成功xx_yy | P-NEW-15 | — | PC covered；mobile-not-applicable |
| AC-046 | 新画布换背购买出现xx_yy | P-NEW-16 | M-NEW-14 | PC covered；mobile covered |
| AC-047 | 新画布换背zz购买成功xx_yy | P-NEW-16 | M-NEW-14 | PC covered；mobile covered |

---

## page_ref 与 selector 表

| page_ref | selector / 说明 |
|---|---|
| `states.mobile_canvas_default` | 移动端画布根状态，含 `li.mobile-primary-panel__tab`、`button[aria-label='Layer']` |
| `states.mobile_canvas_default.buttons.photo_enhancer` | `button.tool-card:has-text('Photo Enhancer')` |
| `states.mobile_canvas_default.buttons.magic_eraser` | `button.tool-card:has-text('Magic Eraser')` |
| `states.mobile_canvas_default.buttons.ai_image_extender` | `button.tool-card:has-text('AI Image Extender')` |
| `stats_first10_20260917.verified_states.mobile_canvas_anonymous_credits_empty_register` | 匿名 0 credits 注册链路（mobile_canvas_v9.yaml） |
| `stats_first10_20260917.verified_states.mobile_canvas_free_credits_empty_purchase` | 免费 0 credits 购买链路（mobile_canvas_v9.yaml） |
| `stats_first10_20260917.verified_states.mobile_canvas_debug_skip_purchase_success` | Debug 跳过真实购买成功链路（mobile_canvas_v9.yaml） |
| `pc_canvas_stats_11_20_20260918` | `/create -> Start from a Photo -> test_images/1K.jpg -> /agent?pid=*` |
| `pc_canvas_anonymous_enhance_register` | 匿名 Credits:0 -> Enhance -> Ultra HD Mode -> Enhance |
| `pc_canvas_register_success` | 注册弹窗 -> 随机唯一邮箱 + `123456` -> Sign up |
| `pc_canvas_purchase_debug_skip_success` | 购买面板 -> DEBUG -> `Debug: 跳过真实购买` |
| `pc_canvas_stats_16_25_correct_landing` | `/tools/photo-enhancer`、`/tools/background-remover`、`/tools/magic-eraser-with-ai-detection`、`/it/ai-replace`、`/pt/ferramentas/expandir-imagem-ia` |
| `pc_canvas_stats_26_31_38_41_correct_landing` | `/ai-replace/add-smile-to-photo`、`/body-editor`、`/hair-editor/virtual-hair-color-try-on`、`/ai-background`、`/tools/gaussian-blur` |
| `pc_canvas_stats_34_37_42_47_correct_landing_20260920` | `/image-to-image-ai`、`/ai-image-generator`、`/tools/photo-restoration`、`/tools/add-hearts-to-photo`、`/tools/background-changer` |
| `pc_canvas_stat15_result_image_download_recheck_20260920` | 结果图下载复核状态 |

---

## 依赖缺口与风险

- **Allure 分组渲染风险**：`epic` 必须只取 `PC端` / `移动端` 两个值；若脚本使用其他 epic，报告会多出第三类，视为不符合本轮要求。
- **真实支付风险**：购买成功用例必须使用 Debug“跳过真实购买”；支付面板无该按钮时用例失败，禁止点真实付款。
- **账号状态风险**：注册统计需匿名 0 credits；购买出现需免费 0 credits；购买成功需 Debug 开关，账号状态与用例前置必须一致。
- **移动端模拟风险**：必须验证 pointer coarse=true、hover none=true、`li.mobile-primary-panel__tab` 存在，否则不是真实移动端布局。
- **不适用功能**：移动端无 AI背景、贴纸功能，38/39、44/45 移动端不建用例；不得用 Background Remover 或 Insert 面板事件替代。
- **已知 bug/gap**：11、12/13、22/23 移动端分别按 blocked_by_gap / blocked_by_bug 管理，脚本阶段不得改成通过。
- **URL 缺口**：32/33 AI滤镜入口仍需用户补充，补齐前保持 skipped。
- **频率断言**：每条用例都要断言目标 `sendGaEvent=1` 且 `debug 统计=1`；0 或 >=2 均失败。





