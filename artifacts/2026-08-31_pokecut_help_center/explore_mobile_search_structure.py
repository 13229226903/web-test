# -*- coding: utf-8 -*-
"""移动端搜索结果容器结构复探。"""
import json
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"

def norm(s): return " ".join((s or "").split())

def main():
    R = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        mctx = browser.new_context(viewport={"width": 375, "height": 812}, locale="en-US")
        mctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
        mp = mctx.new_page()
        mp.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        mp.wait_for_timeout(8000)
        inp = mp.locator('input[placeholder*="Search by keyword"]').first
        inp.scroll_into_view_if_needed()
        inp.fill("credits")
        mp.wait_for_timeout(400)
        mp.keyboard.press("Enter")
        mp.wait_for_timeout(3000)
        R = mp.evaluate("""() => {
            const n = window.__norm;
            // 所有含 results 文本的容器
            const heads = Array.from(document.querySelectorAll('*')).filter(el => /results for/i.test(n(el.textContent)) && el.children.length <= 2).slice(0,5).map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, text:n(el.textContent).slice(0,80)}));
            // 所有可滚动元素
            const scrollables = Array.from(document.querySelectorAll('*')).filter(el => el.scrollHeight > el.clientHeight + 5 && el.clientHeight > 80).slice(0,15).map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, scrollH:el.scrollHeight, clientH:el.clientHeight}));
            // search-panel 类名元素
            const panels = Array.from(document.querySelectorAll('[class*="search-panel"], [class*="search"]')).map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, scrollH:el.scrollHeight, clientH:el.clientHeight})).slice(0,10);
            return {heads, scrollables, panels};
        }""")
        print(json.dumps(R, ensure_ascii=False, indent=2))
        mp.screenshot(path=r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\shots\09_mobile_search_structure.png", full_page=True)
        mctx.close()
        browser.close()

if __name__ == "__main__":
    main()
