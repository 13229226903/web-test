# -*- coding: utf-8 -*-
"""Playwright MCP 驱动 REPL（streamable HTTP 版）：stdin 逐行读 JSON {"tool":..,"args":{..}}。"""
import asyncio, base64, json, sys, time
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://127.0.0.1:8931/mcp"

def parse_args():
    out = Path(r"D:\Test\web-test\artifacts\2026-09-14_stable_regression_all_archived\evidence\mcp_drift_20260914")
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--out" and i + 1 < len(args):
            out = Path(args[i + 1])
    out.mkdir(parents=True, exist_ok=True)
    return out

OUT = parse_args()
IMG_N = {"n": 0}

def render(result, limit=2600):
    lines = []
    for c in result.content:
        t = getattr(c, "type", None)
        if t == "text":
            lines.append(c.text[:limit] + ("…[truncated]" if len(c.text) > limit else ""))
        elif t == "image":
            IMG_N["n"] += 1
            p = OUT / f"img_{IMG_N['n']:03d}.png"
            p.write_bytes(base64.b64decode(c.data))
            lines.append(f"[image saved] {p}")
        else:
            lines.append(f"[{t}] {str(c)[:300]}")
    if getattr(result, "isError", False):
        lines.insert(0, "!! isError=true")
    return "\n".join(lines)

async def main():
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("MCP_READY", flush=True)
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                except Exception as e:
                    print(f"BAD_JSON {e}", flush=True); continue
                if req.get("cmd") == "quit":
                    break
                if req.get("cmd") == "tools":
                    tools = await session.list_tools()
                    print("TOOLS " + json.dumps([t.name for t in tools.tools], ensure_ascii=False), flush=True)
                    continue
                tool, args = req.get("tool"), req.get("args") or {}
                t0 = time.time()
                try:
                    res = await session.call_tool(tool, args)
                    body = render(res, req.get("limit", 2600))
                    print(f"BEGIN {tool} ({time.time()-t0:.1f}s)", flush=True)
                    print(body, flush=True)
                    print("END", flush=True)
                except Exception as e:
                    print(f"ERROR {tool}: {type(e).__name__}: {e}", flush=True)

asyncio.run(main())