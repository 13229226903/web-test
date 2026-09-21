# PC 功能入口补采结果（第 34/35、36/37、42/43、44/45、46/47 条）

日期：2026-09-20  
驱动：Playwright MCP only  
说明：均从对应功能介绍页进入，使用 `test_images/1K.jpg`；购买成功仅使用 Debug“跳过真实购买（查看统计项用）”，不执行真实付款。

| 原文序号 | 原文标题 | URL入口 | 触发交互 | 实际事件 | 期望事件 | 结论 |
|---:|---|---|---|---|---|---|
| 34 | 新画布图生图购买出现xx_yy | `/image-to-image-ai` | 首屏上传 `test_images/1K.jpg` -> 点击 Generate -> 进入 `/agent?pid=*` 并自动触发购买 | `新画布图生图购买出现en_image-to-image-ai` | `新画布图生图购买出现xx_yy`，本次 `xx_yy=en_image-to-image-ai` | ✅ 一致 |
| 35 | 新画布图生图zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布图生图年ultra购买成功en_image-to-image-ai` | `新画布图生图zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ 一致 |
| 36 | 新画布文生图购买出现xx_yy | `/ai-image-generator` | 使用默认提示词 -> 点击 Generate -> 进入 `/agent?pid=*` 并自动触发购买 | `新画布文生图购买出现en_ai-image-generator` | `新画布文生图购买出现xx_yy`，本次 `xx_yy=en_ai-image-generator` | ✅ 一致 |
| 37 | 新画布文生图zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布文生图年ultra购买成功en_ai-image-generator` | `新画布文生图zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ 一致 |
| 42 | 新画布照片修复购买出现xx_yy | `/tools/photo-restoration` | 首屏上传 -> 进入画布后保持默认选中的 `Old Photo Mode` -> 直接点击 `Enhance` -> 触发购买 | `新画布照片修复购买出现en_photo-restoration` | `新画布照片修复购买出现xx_yy`，本次 `xx_yy=en_photo-restoration` | ✅ 一致 |
| 43 | 新画布照片修复zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布照片修复年ultra购买成功en_photo-restoration` | `新画布照片修复zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ 一致 |
| 44 | 新画布贴纸购买出现xx_yy | `/tools/add-hearts-to-photo` | 免费登录态 -> 首屏上传 -> 进入画布 -> Sticker 自动弹出 -> Valentine 2 -> 第二个 VIP 贴纸 -> 按住鼠标左键框选全部图层 -> Download VIP | `新画布贴纸购买出现en_add-hearts-to-photo` | `新画布贴纸购买出现xx_yy`，本次 `xx_yy=en_add-hearts-to-photo` | ✅ 一致 |
| 45 | 新画布贴纸zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布贴纸年ultra购买成功en_add-hearts-to-photo` | `新画布贴纸zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ 一致 |
| 46 | 新画布换背购买出现xx_yy | `/tools/background-changer` | 首屏上传 -> 进入 `/agent?pid=*` 后自动触发换背购买 | `新画布换背购买出现en_background-changer` | `新画布换背购买出现xx_yy`，本次 `xx_yy=en_background-changer` | ✅ 一致 |
| 47 | 新画布换背zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布换背年ultra购买成功en_background-changer` | `新画布换背zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ 一致 |

## 证据文件

- `evidence/console_pc_correct_entry_image_to_image_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_image_to_image_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_text_to_image_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_text_to_image_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_photo_restoration_purchase_appearance_debug.log`（旧路径记录，已由下方复核日志修正）
- `evidence/console_pc_correct_entry_photo_restoration_purchase_success_debug.log`（旧路径记录，已由下方复核日志修正）
- `evidence/console_stat42_43_recheck_photo_restoration_submit_default_old_photo_debug.log`
- `evidence/console_pc_correct_entry_sticker_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_sticker_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_background_changer_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_background_changer_purchase_success_debug.log`

本批新增完成 10 条，全部一致通过。42/43 首次记录为 gap 的原因是执行路径未保持 SEO 入口默认选中的 `Old Photo Mode`，复核后直接从 `/tools/photo-restoration` 进入画布、保持默认 `Old Photo Mode` 并点击 `Enhance`，实际事件恢复为 `新画布照片修复...en_photo-restoration`。

## 42/43 复核结论

- 日期：2026-09-20 10:03:53
- 复核路径：`/tools/photo-restoration` -> 上传 `test_images/1K.jpg` -> 进入 `/agent?pid=*`，画布自动打开 AI Enhancer，默认选中 `Old Photo Mode`，未切换其他模式 -> 直接点击 `Enhance`。
- 复核事件：`新画布照片修复购买出现en_photo-restoration`、`新画布照片修复年ultra购买成功en_photo-restoration`。
- 复核证据：`evidence/console_stat42_43_recheck_photo_restoration_submit_default_old_photo_debug.log`、`shots/stat42_43_photo_restoration_default_old_photo_purchase_success.png`。
