# stat15 结果图下载复核摘要

日期：2026-09-20 10:42:57  
驱动：Playwright MCP only  
说明：按用户确认路径复核，下载对象是 Enhanced 结果图层，不是原图。

## 复核路径

1. `/create`
2. `Start from a Photo`
3. 上传 `test_images/1K.jpg`
4. 进入 `/agent?pid=*`
5. 点击 `Enhance`
6. 保持 `Standard Mode`，点击 `Enhance` 生成成功
7. 选中结果图层 `图片 1 (Enhanced)` / `data-element-id=el-1789871766452-2ajt7cb`
8. 点击选中结果图层后的工具栏下载按钮 `button.group/download-left`

## 实际 Console 事件

- `sendGaEvent 无限画布页单图下载`
- `sendGaEvent 下载成功`
- `sendGaEvent 无限画布页画质增强ultra功能图片下载保存`
- `sendGaEvent 无限画布页画质增强2K-ultra模型图片下载保存`

其中目标需求项为「无限画布页xx功能图片下载保存」，本次 `xx=画质增强ultra`，实际事件名与需求一致。

## 证据

- `evidence/console_stat15_recheck_result_download_mcp_raw.log`
- 原始 MCP console log：`.playwright-mcp/console-2026-09-20T02-28-41-316Z.log`

## 限制

点击下载后 Playwright MCP transport closed；当前 raw MCP log 已包含 `sendGaEvent`，但未能再调用 `browser_console_messages(level=debug)` 保存同次 `debug 统计：...` 成对输出。按用户规则记录为 MCP blocker，后续如 MCP 恢复可补采 debug 成对日志。
