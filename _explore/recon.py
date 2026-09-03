# -*- coding: utf-8 -*-
"""Recon: 登录后逐个打开 4 个工具，转储面板 DOM + 截图，不提交。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import login, open_tool, dump_ui, shot, log, dismiss
from playwright.sync_api import sync_playwright

TOOLS = ["Remove Background", "AI Background", "AI Expand", "AI Erase"]

with sync_playwright() as pw:
    browser, ctx, page = login(pw)
    for t in TOOLS:
        tag = t.replace(" ", "_")
        log("==== RECON", t, "====")
        try:
            page2 = ctx.new_page()
            page2.goto("http://10.17.1.66:3001/create")
            page2.wait_for_timeout(4000)
            dismiss(page2)
            url = open_tool(page2, t)
            page2.wait_for_timeout(4000)
            dump_ui(page2, tag)
            shot(page2, f"recon_{tag}")
            page2.close()
        except Exception as e:
            log("RECON FAIL", t, repr(e))
            try:
                page2.screenshot(path=os.path.join(os.path.dirname(__file__), f"fail_{tag}.png"))
            except Exception:
                pass
    browser.close()
    log("recon done")
