# -*- coding: utf-8 -*-
"""定向复探：热门标签点击触发搜索 + 移动端搜索结果滚动。"""
import json
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"

def norm(s): return " ".join((s or "").split())

def main():
    R = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        ctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
        page = ctx.new_page()

        # 热门标签点击
        page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(8000)
        tag = page.locator("button:has-text('Credits')").first
        tag.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        try:
            tag.click()
        except Exception:
            tag.dispatch_event("click")
        page.wait_for_timeout(2500)
        R["tag_click"] = page.evaluate("""() => {
            const n = window.__norm;
            const inp = document.querySelector('input[placeholder*="Search by keyword"]');
            const body = n(document.body.textContent);
            const m = body.match(/(\\d+)\\s+results?\\s+for/);
            return {
                url: location.href,
                input_value: inp ? inp.value : null,
                results_count_text: m ? m[0] : null,
            };
        }""")
        print("[TAG CLICK]", json.dumps(R["tag_click"], ensure_ascii=False))

        # 移动端搜索滚动
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
        R["mobile_search"] = mp.evaluate("""() => {
            const n = window.__norm;
            const body = n(document.body.textContent);
            const m = body.match(/(\\d+)\\s+results?\\s+for/);
            const results = document.querySelector('div.help-v2-search-panel__results');
            return {
                url: location.href,
                results_count_text: m ? m[0] : null,
                results_scrollH: results ? results.scrollHeight : null,
                results_clientH: results ? results.clientHeight : null,
                scrollable: results ? results.scrollHeight > results.clientHeight + 5 : false,
            };
        }""")
        print("[MOBILE SEARCH]", json.dumps(R["mobile_search"], ensure_ascii=False))
        mp.screenshot(path=r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\shots\08_mobile_search_credits.png", full_page=True)
        mctx.close()
        browser.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_tag_mobile_search.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n[DONE]")

if __name__ == "__main__":
    main()
