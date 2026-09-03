# -*- coding: utf-8 -*-
"""快速探测搜索关键词命中数，用于 L5 参数化取值。"""
import json
from playwright.sync_api import sync_playwright
BASE = "http://10.17.1.66:3001"
def main():
    R = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        c = b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
        c.add_init_script("window.__norm=(s)=>(s||'').replace(/\\s+/g,' ').trim();")
        pg = c.new_page()
        pg.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(7000)
        for kw in ["language", "refund", "download", "subscription", "unsubscribe"]:
            pg.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
            pg.wait_for_timeout(5000)
            inp = pg.locator('input[placeholder*="Search by keyword"]').first
            inp.scroll_into_view_if_needed()
            inp.fill(kw)
            pg.wait_for_timeout(300)
            pg.keyboard.press("Enter")
            pg.wait_for_timeout(2200)
            data = pg.evaluate("""() => {
                const n = window.__norm;
                const body = n(document.body.textContent);
                const m = body.match(/(\\d+)\\s+results?\\s+for/);
                const items = Array.from(document.querySelectorAll('button[class*="search-panel__result"], [class*="search-panel__result"]')).length;
                return {count_text: m ? m[0] : null, result_item_count: items};
            }""")
            R[kw] = data
            print(kw, json.dumps(data, ensure_ascii=False))
        b.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_search_counts.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
if __name__ == "__main__":
    main()
