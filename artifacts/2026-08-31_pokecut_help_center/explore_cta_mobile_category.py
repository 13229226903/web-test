# -*- coding: utf-8 -*-
"""定向复探：底部 Contact us 点击弹窗 + 移动端分类标签横向滑动。"""
import json
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"

def norm(s): return " ".join((s or "").split())

def vue_click(page, locator):
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    handle = locator.element_handle()
    if handle:
        handle.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
    page.wait_for_timeout(1200)

def main():
    R = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        ctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
        page = ctx.new_page()

        # 底部 Contact us 点击
        page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(8000)
        btn = page.locator("button.help-v2-support-cta-section__button").first
        before = page.evaluate("() => { const d = document.querySelector('[role=dialog], dialog[open], [class*=\"modal\"], [class*=\"popup\"], [class*=\"ticket\"]'); return d ? {found:true, cls:d.className, text:window.__norm(d.textContent).slice(0,200)} : {found:false}; }")
        vue_click(page, btn)
        after = page.evaluate("""() => {
            const dialogs = Array.from(document.querySelectorAll('[role=dialog], dialog[open], [aria-modal="true"], [class*="modal"], [class*="popup"], [class*="ticket"], [class*="dialog"]'))
                .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
                .map(el => ({cls: el.className, text: window.__norm(el.textContent).slice(0,300)}));
            return {dialogs};
        }""")
        R["bottom_contact"] = {"before": before, "after": after}
        print("[BOTTOM CONTACT BEFORE]", json.dumps(before, ensure_ascii=False))
        print("[BOTTOM CONTACT AFTER]", json.dumps(after, ensure_ascii=False))
        page.screenshot(path=r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\shots\10_bottom_contact_after_click.png", full_page=True)

        # 移动端分类标签横向滑动
        mctx = browser.new_context(viewport={"width": 375, "height": 812}, locale="en-US")
        mctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
        mp = mctx.new_page()
        mp.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        mp.wait_for_timeout(8000)
        # 点击一个分类卡片进入分类
        card = mp.locator("button[class*='category-card']:has-text('Plans, Credits & Billing')").first
        vue_click(mp, card)
        mp.wait_for_timeout(800)
        R["mobile_category"] = mp.evaluate("""() => {
            const n = window.__norm;
            const tags = Array.from(document.querySelectorAll('[class*="mobile"] button, [class*="tab"], [class*="nav-item"], [class*="category"] button'))
                .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && n(el.textContent).length > 0 && n(el.textContent).length < 60; })
                .slice(0, 25)
                .map(el => ({tag:el.tagName.toLowerCase(), text:n(el.textContent), cls:el.className}));
            // 查找可横向滚动的标签容器
            const scrollable = Array.from(document.querySelectorAll('*')).filter(el => el.scrollWidth > el.clientWidth + 5 && el.clientWidth > 100).slice(0,10)
                .map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, scrollW:el.scrollWidth, clientW:el.clientWidth}));
            return {tags, scrollable};
        }""")
        print("[MOBILE CATEGORY]", json.dumps(R["mobile_category"], ensure_ascii=False))
        mp.screenshot(path=r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\shots\11_mobile_category_faq.png", full_page=True)
        mctx.close()
        browser.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_cta_mobile_category.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n[DONE]")

if __name__ == "__main__":
    main()
