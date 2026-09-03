# -*- coding: utf-8 -*-
"""桌面搜索命中结果条目结构。"""
import json
from playwright.sync_api import sync_playwright
BASE="http://10.17.1.66:3001"
def main():
    R={}
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        c=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
        c.add_init_script("window.__norm=(s)=>(s||'').replace(/\\s+/g,' ').trim();")
        pg=c.new_page()
        pg.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(7000)
        inp=pg.locator('input[placeholder*="Search by keyword"]').first
        inp.scroll_into_view_if_needed(); inp.fill("credits"); pg.wait_for_timeout(300); pg.keyboard.press("Enter"); pg.wait_for_timeout(2500)
        R=pg.evaluate("""() => {
            const n=window.__norm;
            const results=document.querySelector('div.help-v2-search-panel__results');
            const kids=results ? Array.from(results.children).slice(0,4).map(el=>({tag:el.tagName.toLowerCase(), cls:el.className, text:n(el.textContent).slice(0,160)})) : [];
            const headers=Array.from(document.querySelectorAll('div.help-v2-search-panel__header *, div.help-v2-search-panel__header')).map(el=>({tag:el.tagName.toLowerCase(), cls:el.className, text:n(el.textContent).slice(0,120)})).slice(0,5);
            return {results_container_cls: results? results.className : null, kid_count: results? results.children.length : 0, kids, headers};
        }""")
        print(json.dumps(R, ensure_ascii=False, indent=2))
        b.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_desktop_result_item.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
if __name__=="__main__":
    main()
