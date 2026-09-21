# PC 功能入口补采结果（第 26、27、28、29、30、31、38、39、40、41 条）

日期：2026-09-18  
驱动：Playwright MCP only  
说明：均从对应功能介绍页进入，点击首屏上传按钮，选择 `test_images/1K.jpg`，进入 PC 无限画布；购买成功仅使用 Debug“跳过真实购买（查看统计项用）”，不真实付款。

| 原文序号 | 原文标题 | 正确入口 | 触发交互 | 出现事件 | 成功事件 | 结论 |
|---:|---|---|---|---|---|---|
| 26 | 新画布脸部购买出现xx_yy | `/ai-replace/add-smile-to-photo`，实际跳转 `/face-editor/add-smile-to-photo` | 首屏上传 -> `/agent?pid=*` -> Portrait Editor -> Face -> Remove Acne -> Generate | `新画布脸部购买出现en_add-smile-to-photo` | — | ✅ |
| 27 | 新画布脸部zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | 同上 | `新画布脸部年ultra购买成功en_add-smile-to-photo` | ✅ |
| 28 | 新画布身材购买出现xx_yy | `/body-editor` | 首屏上传 -> `/agent?pid=*` -> Body -> Natural Breast -> Generate | `新画布身材购买出现en_body-editor` | — | ✅ |
| 29 | 新画布身材zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | 同上 | `新画布身材年ultra购买成功en_body-editor` | ✅ |
| 30 | 新画布发型购买出现xx_yy | `/hair-editor/virtual-hair-color-try-on` | 首屏上传 -> `/agent?pid=*` -> Hair -> Blonde -> Generate | `新画布发型购买出现en_virtual-hair-color-try-on` | — | ✅ |
| 31 | 新画布发型zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | 同上 | `新画布发型年ultra购买成功en_virtual-hair-color-try-on` | ✅ |
| 38 | 新画布AI背景购买出现xx_yy | `/ai-background` | 首屏上传 -> `/agent?pid=*` -> 自动触发 AI Background 购买 | `新画布AI背景购买出现en_ai-background` | — | ✅ |
| 39 | 新画布AI背景zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | 同上 | `新画布AI背景年ultra购买成功en_ai-background` | ✅ |
| 40 | 新画布背景模糊购买出现xx_yy | `/tools/gaussian-blur` | 首屏上传 -> `/agent?pid=*` -> 自动触发 BG Blur 购买 | `新画布背景模糊购买出现en_gaussian-blur` | — | ✅ |
| 41 | 新画布背景模糊zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | 同上 | `新画布背景模糊年ultra购买成功en_gaussian-blur` | ✅ |

## 证据文件

- `evidence/console_pc_correct_entry_face_add_smile_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_face_add_smile_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_body_editor_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_body_editor_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_hair_editor_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_hair_editor_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_ai_background_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_ai_background_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_gaussian_blur_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_gaussian_blur_purchase_success_debug.log`
