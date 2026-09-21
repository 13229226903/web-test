# 移动端不适用统计：38/39 AI背景、44/45 贴纸

日期：2026-09-20  
驱动：Playwright MCP only

用户确认：移动端没有 AI背景、贴纸功能，因此以下统计不需要在移动端测试，也不应记为 gap 或 bug_candidate。

| 序号 | 原文标题 | 功能 | 移动端结论 | 说明 |
|---:|---|---|---|---|
| 38 | 新画布AI背景购买出现xx_yy | AI背景 | mobile-not-applicable / skipped | 移动端无 AI背景功能 |
| 39 | 新画布AI背景zz购买成功xx_yy | AI背景 | mobile-not-applicable / skipped | 移动端无 AI背景功能 |
| 44 | 新画布贴纸购买出现xx_yy | 贴纸 | mobile-not-applicable / skipped | 移动端无贴纸功能 |
| 45 | 新画布贴纸zz购买成功xx_yy | 贴纸 | mobile-not-applicable / skipped | 移动端无贴纸功能 |

此前第 38/39 尝试 `/ai-background` 时进入的是移动端 Background 面板，实际走到的 `新画布抠图购买出现en_ai-background` 属于 Background Remover，不代表 AI背景功能。按本轮用户确认，38/39 不作为移动端失败或 bug，仅记录为移动端不适用。
