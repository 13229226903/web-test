# 新画布页统计移动端补充探索清单

日期：2026-09-20 10:56:11  
状态：pending_playwright_mcp_restore  
驱动要求：Playwright MCP only；当前会话 MCP transport closed，不能开始探索。

## 结论

“新画布页相关统计”除 PC 外还需要补移动端探索。移动端入口 URL 与 PC 保持一致，不另造入口。

## 待补统计范围

需要按需求中所有「新画布...xx_yy」统计补移动端覆盖，核心范围包括：

- 16/17：`/tools/photo-enhancer`
- 18/19：`/tools/background-remover`
- 20/21：`/tools/magic-eraser-with-ai-detection`
- 22/23：`/it/ai-replace`
- 24/25：`/pt/ferramentas/expandir-imagem-ia`
- 26/27：`/ai-replace/add-smile-to-photo` -> 实际可能跳 `/face-editor/add-smile-to-photo`
- 28/29：`/body-editor`
- 30/31：`/hair-editor/virtual-hair-color-try-on`
- 32/33：AI滤镜，URL仍为跳过；需用户补充后补测
- 34/35：`/image-to-image-ai`
- 36/37：`/ai-image-generator`
- 38/39：`/ai-background`
- 40/41：`/tools/gaussian-blur`
- 42/43：`/tools/photo-restoration`
- 44/45：`/tools/add-hearts-to-photo`
- 46/47：`/tools/background-changer`

## 移动端探索要求

- 使用移动视口 / 移动 UA；入口 URL 同 PC。
- 点击首屏上传按钮 / 生成入口，使用 `test_images/1K.jpg`。
- 进入移动端画布后触发对应功能。
- 购买成功仍只允许使用 Debug“跳过真实购买”。
- Console 验证必须同时满足次数唯一性断言：
  - `sendGaEvent <目标事件>` = 1 次
  - `debug 统计：<目标事件>` = 1 次
  - 稳定窗口内不新增
- `0` 次为漏报 bug；`>=2` 次为多报 bug。
- 若移动端入口跳转到不同画布形态，仍需先验证是否进入移动端画布页；若没有移动端统计事件，记录 gap / bug 前先保存入口、URL、Console 和截图证据。

## 阻塞

- `playwright_mcp_unavailable`: 当前会话 `browser_tabs list` 连续返回 `Transport closed`。
- 恢复条件：Codex/Playwright MCP transport 重新可用，并依次通过：
  1. `browser_tabs list`
  2. `browser_navigate about:blank`
  3. `browser_snapshot`
  4. `browser_console_messages`

