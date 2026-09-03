# -*- coding: utf-8 -*-
"""移动端 FAQ 条目结构复探（open 态 + 答案）。"""
import json
from playwright.sync_api import sync_playwright
BASE="http://10.17.1.66:3001"
def main():
    R={}
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        c=b.new_context(viewport={"width":375,"height":812}, locale="en-US")
        c.add_init_script("window.__norm=(s)=>(s||'').replace(/\\s+/g,' ').trim();")
        pg=c.new_page()
        pg.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(8000)
        # 点击一个分类卡片
        card=pg.locator("button[class*='category-card']:has-text('Getting Started')").first
        card.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
        card.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}))")
        pg.wait_for_timeout(1200)
        R=pg.evaluate("""() => {
            const n=window.__norm;
            const items=Array.from(document.querySelectorAll('article[class*="faq-item"], [class*="mobile-faq-item"]'));
            return items.slice(0,6).map(it=>({
                cls: it.className,
                q: it.querySelector('button[class*="question"]') ? n(it.querySelector('button[class*="question"]').textContent) : null,
                a: it.querySelector('div[class*="answer"], [class*="answer"]') ? n(it.querySelector('div[class*="answer"], [class*="answer"]').textContent) : null,
                open: it.className.includes('open'),
            }));
        }""")
        print(json.dumps(R, ensure_ascii=False, indent=2))
        # 展开第二条
        q2=pg.locator("button.help-v2-mobile-faq-item__question").nth(1)
        q2.scroll_into_view_if_needed(); pg.wait_for_timeout(200)
        q2.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}))")
        pg.wait_for_timeout(800)
        R2=pg.evaluate("""() => {
            const items=Array.from(document.querySelectorAll('[class*="mobile-faq-item"], article[class*="faq-item"]'));
            return items.slice(0,6).map(it=>({cls:it.className, open:it.className.includes('open')}));
        }""")
        print("AFTER CLICK 2nd:", json.dumps(R2, ensure_ascii=False))
        b.close()
    json.dump({"initial":R, "after_click_2nd":R2}, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_mobile_faq_open.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
if __name__=="__main__":
    main()
