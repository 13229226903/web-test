# PC 功能入口补采结果（第 16-25 条）

日期：2026-09-18  
驱动：Playwright MCP only  
说明：之前从 `/create` 直进画布是错误入口；本轮从对应 SEO 功能介绍页进入后补采，10 条购买相关统计均通过。

| 原文序号 | 原文标题 | 正确入口 | 出现事件 | 成功事件 | 结论 |
|---:|---|---|---|---|---|
| 16 | 新画布增强购买出现xx_yy | `/tools/photo-enhancer` | `新画布增强购买出现en_photo-enhancer` | `新画布增强年ultra购买成功en_photo-enhancer` | ✅ |
| 17 | 新画布增强zz购买成功xx_yy | `/tools/photo-enhancer` | 同上 | 同上 | ✅ |
| 18 | 新画布抠图购买出现xx_yy | `/tools/background-remover` | `新画布抠图购买出现en_background-remover` | `新画布抠图年ultra购买成功en_background-remover` | ✅ |
| 19 | 新画布抠图zz购买成功xx_yy | `/tools/background-remover` | 同上 | 同上 | ✅ |
| 20 | 新画布消除购买出现xx_yy | `/tools/magic-eraser-with-ai-detection` | `新画布消除购买出现en_magic-eraser-with-ai-detection` | `新画布消除年ultra购买成功en_magic-eraser-with-ai-detection` | ✅ |
| 21 | 新画布消除zz购买成功xx_yy | `/tools/magic-eraser-with-ai-detection` | 同上 | 同上 | ✅ |
| 22 | 新画布改图购买出现xx_yy | `/it/ai-replace` | `新画布改图购买出现it_ai-replace` | `新画布改图年ultra购买成功it_ai-replace` | ✅ |
| 23 | 新画布改图zz购买成功xx_yy | `/it/ai-replace` | 同上 | 同上 | ✅ |
| 24 | 新画布扩图购买出现xx_yy | `/pt/ferramentas/expandir-imagem-ia` | `新画布扩图购买出现pt_expandir-imagem-ia` | `新画布扩图年ultra购买成功pt_expandir-imagem-ia` | ✅ |
| 25 | 新画布扩图zz购买成功xx_yy | `/pt/ferramentas/expandir-imagem-ia` | 同上 | 同上 | ✅ |

购买成功均通过 DEBUG 面板“跳过真实购买（查看统计项用）”与 checkout 的 `Debug: 跳过真实购买` 触发，未真实扣款。

## 证据文件

- `evidence/console_pc_correct_entry_en_photo_enhancer_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_en_photo_enhancer_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_en_background_remover_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_en_background_remover_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_en_magic_eraser_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_en_magic_eraser_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_it_ai_replace_generate_debug.log`
- `evidence/console_pc_correct_entry_it_ai_replace_purchase_success_debug.log`
- `evidence/console_pc_correct_entry_pt_expand_purchase_appearance_debug.log`
- `evidence/console_pc_correct_entry_pt_expand_purchase_success_debug.log`
