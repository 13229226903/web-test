# 移动端模拟设备前置确认

日期：$now  
结论：当前 Playwright MCP 浏览器上下文**不是真实移动端模拟**，不能用于新画布页移动端统计探索。

## 当前实测

- URL: `http://10.17.1.66:3001/agent?pid=360af2cc-fab0-419c-807c-c4fd62b4a050#`
- viewport: `390x844`
- DPR: `1`
- UA（通过 init script 注入）: iPhone Safari UA
- `navigator.platform`: `iPhone`
- `navigator.maxTouchPoints`: `5`
- `matchMedia('(pointer: coarse)').matches`: `false`
- `matchMedia('(hover: none)').matches`: `false`
- `li.mobile-primary-panel__tab`: 不存在
- `button.mobile-primary-panel__upgrade`: 不存在
- `button[aria-label='Layer']`: 不存在
- 页面仍显示桌面无限画布组件：`Chat to edit`、`AI Enhancer` 等

## 判定

`browser_resize` 只改变 viewport，`addInitScript` 只改 navigator 字段；二者不会设置 Playwright 的 `isMobile` / `hasTouch` / deviceScaleFactor / pointer/hover 媒体特性。

因此当前页面是“桌面 Chrome 窄视口 + UA 伪装”，不是移动端布局，不符合规则。

## 恢复/整改要求

Playwright MCP 需要以移动端上下文启动，可选：

- `--device "iPhone 13"` 或类似设备预设
- 或 `--mobile`

当前 `C:\Users\liangjinrun\.codex\config.toml` 的 Playwright MCP 配置只有：

```toml
[mcp_servers.playwright]
command = 'D:\Program Files\nodejs\node.exe'
args = ["C:/Users/liangjinrun/AppData/Roaming/npm/node_modules/@playwright/mcp/cli.js", "--browser=chrome", "--user-data-dir=D:/playwright-cache/mcp-profile"]
```

已于 2026-09-20 修改为配置 `--device "iPhone 13"`；需要重启 Codex / Playwright MCP 后生效。

## 下一步

需要重启 Codex / Playwright MCP，使移动端 device 配置生效；重启后必须重新做强 preflight，并再次确认：

1. `pointer: coarse = true`
2. `hover: none = true`
3. 移动端画布组件存在，例如 `li.mobile-primary-panel__tab`
4. 页面不再使用桌面无限画布布局

满足以上条件后才能开始移动端新画布统计探索。

## 配置修改记录

- 配置路径：`C:\Users\liangjinrun\.codex\config.toml`
- 备份：`C:\Users\liangjinrun\.codex\config.toml.bak-20260920-mobile`
- 新增参数：`--device`, `iPhone 13`
- 生效条件：重启 Codex / Playwright MCP；当前已运行会话不会热加载新参数。
