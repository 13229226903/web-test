# scripts/mcp — Playwright MCP 驱动

页面复探阶段（page-map-sync）用 Playwright MCP 驱动浏览器时的可复用入口。

## 启动 MCP 服务

```powershell
npx -y @playwright/mcp@latest --port 8931 --host 127.0.0.1 --allowed-hosts * --isolated
```

- `--allowed-hosts *`：不设会返回 403（Host 校验）
- `--isolated`：内存态 profile，避免污染本机浏览器配置
- 移动端探索：加设备模拟参数（如 `--mobile`，或等价 device emulation）——viewport / UA / `is_mobile` / `touch` 是 context 级参数，
  缺了会以桌面 context 打开，页面渲染 PC 版且**不报错**；导航后先跑 viewport guard 自检再开始探索。

## 驱动会话

```powershell
python scripts/mcp/mcp_drive_http.py --out artifacts/<task_id>/evidence/mcp_<日期>
# stdin 逐行读 JSON：{"tool":"browser_run_code_unsafe","args":{"code":"async (page) => { ... }"}}
# 特殊行：{"cmd":"tools"} 列工具；{"cmd":"quit"} 退出
```

- `mcp_drive_http.py`：streamable HTTP（`http://127.0.0.1:8931/mcp`），当前 npx 版本走这个
- `mcp_drive.py`：旧版 SSE（`/sse`）驱动，仅在 SSE 端点可用时使用

## 注意

- 交互式会话需 PTY 保持 stdin；批处理可 `Get-Content req.jsonl | python scripts/mcp/mcp_drive_http.py`（无行长度限制）
- 中文/emoji 输出需 `PYTHONIOENCODING=utf-8:replace`，否则可能 UnicodeEncodeError
- 一次性探针（`explore_*.js`、`patch_*.py` 等）不再放 `_explore/`；按任务归档到 `artifacts/<task_id>/evidence/`