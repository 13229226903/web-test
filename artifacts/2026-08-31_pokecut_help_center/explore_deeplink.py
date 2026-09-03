# -*- coding: utf-8 -*-
"""定向复探：Contact us 深链自动展开 + Popular questions 区块。"""
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

        # 深链
        url = f"{BASE}/help?category=commercial-safety-support&question=commercial-safety-support-4#contact-us"
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(8000)
        R["deeplink"] = page.evaluate("""() => {
            const n = window.__norm;
            const navs = Array.from(document.querySelectorAll('button[class*="faq-section__nav-item"]'));
            const active = navs.find(x => x.className.includes('active'));
            const items = Array.from(document.querySelectorAll('article[class*="faq-item"]'));
            const openItems = items.filter(it => it.className.includes('open')).map(it => n(it.querySelector('button[class*="question"]')?.textContent));
            const openAnswers = items.filter(it => it.className.includes('open')).map(it => n(it.querySelector('div[class*="answer"]')?.textContent));
            return {
                url: location.href,
                active_nav: active ? n(active.textContent) : null,
                open_questions: openItems,
                open_answers: openAnswers,
                total_items: items.length,
            };
        }""")
        print("[DEEPLINK]", json.dumps(R["deeplink"], ensure_ascii=False))
        page.screenshot(path=r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\shots\07_deeplink_contact.png", full_page=True)

        # Popular questions 区块
        page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(8000)
        R["popular_section"] = page.evaluate("""() => {
            const n = window.__norm;
            const body = n(document.body.textContent);
            const heads = Array.from(document.querySelectorAll('h2,h3,span,p')).filter(el => /Popular questions/i.test(n(el.textContent))).map(el => ({tag:el.tagName.toLowerCase(), text:n(el.textContent), cls:el.className}));
            return {has_popular_questions: /Popular questions/i.test(body), heads: heads.slice(0,5)};
        }""")
        print("[POPULAR]", json.dumps(R["popular_section"], ensure_ascii=False))

        browser.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_deeplink.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n[DONE]")

if __name__ == "__main__":
    main()
