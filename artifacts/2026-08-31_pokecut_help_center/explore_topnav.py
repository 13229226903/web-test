# -*- coding: utf-8 -*-
"""定向复探：各页面顶部导航是否存在 Contact us，及帮助页 header 结构。"""
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
        for path in ["/", "/help", "/create", "/tools/ai-photo-enhancer"]:
            try:
                page.goto(f"{BASE}{path}", wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(6000)
                info = page.evaluate("""() => {
                    const n = window.__norm;
                    const all = Array.from(document.querySelectorAll('header, nav, [class*="header"], [class*="navbar"], [class*="nav-bar"], [class*="top-nav"]'));
                    const withLinks = all.map(h => {
                        const links = Array.from(h.querySelectorAll('a,button')).map(x => ({tag:x.tagName.toLowerCase(), text:n(x.textContent), href:x.getAttribute('href')||null})).filter(x=>x.text);
                        return {tag:h.tagName.toLowerCase(), cls:h.className, links};
                    }).filter(x => x.links.length > 0);
                    // 全页找 Contact us
                    const contactEls = Array.from(document.querySelectorAll('a,button')).filter(el => /Contact us/i.test(n(el.textContent)));
                    return {url: location.href, headers_with_links: withLinks, contact_els: contactEls.map(el => ({tag:el.tagName.toLowerCase(), text:n(el.textContent), href:el.getAttribute('href')||null, cls:el.className}))};
                }""")
                R[path] = info
                print(f"=== {path} ===")
                print("  contact els:", json.dumps(info["contact_els"], ensure_ascii=False))
                print("  headers with links:", json.dumps(info["headers_with_links"], ensure_ascii=False)[:2000])
            except Exception as e:
                R[path] = {"error": str(e)}
                print(f"=== {path} ERROR: {e}")
        browser.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_topnav.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n[DONE]")

if __name__ == "__main__":
    main()
