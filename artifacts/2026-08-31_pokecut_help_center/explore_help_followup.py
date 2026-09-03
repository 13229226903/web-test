# -*- coding: utf-8 -*-
"""定向复探：顶部导航 Contact us + 搜索排序文案/结果容器结构 + 空态结构。"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center")
SHOTS = OUT / "shots"

def norm(s): return " ".join((s or "").split())

def main():
    R = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        ctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
        page = ctx.new_page()

        # ---- 首页顶部导航全结构 ----
        page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(7000)
        R["home_header"] = page.evaluate("""() => {
            const n = window.__norm;
            const headers = Array.from(document.querySelectorAll('header, nav, [class*="header"], [class*="navbar"], [class*="nav-"]'));
            return headers.map(h => {
                const links = Array.from(h.querySelectorAll('a,button')).map(x => ({tag:x.tagName.toLowerCase(), text:n(x.textContent), href:x.getAttribute('href')||null, cls:x.className}));
                return {tag:h.tagName.toLowerCase(), cls:h.className, links};
            }).filter(x => x.links.length > 0);
        }""")
        print("[HOME HEADER]", json.dumps(R["home_header"], ensure_ascii=False))

        # ---- /help 页面顶部导航 ----
        page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(7000)
        R["help_header"] = page.evaluate("""() => {
            const n = window.__norm;
            const headers = Array.from(document.querySelectorAll('header, nav, [class*="header"], [class*="navbar"], [class*="nav-"]'));
            return headers.map(h => {
                const links = Array.from(h.querySelectorAll('a,button')).map(x => ({tag:x.tagName.toLowerCase(), text:n(x.textContent), href:x.getAttribute('href')||null, cls:x.className}));
                return {tag:h.tagName.toLowerCase(), cls:h.className, links};
            }).filter(x => x.links.length > 0);
        }""")
        print("[HELP HEADER]", json.dumps(R["help_header"], ensure_ascii=False))

        # ---- 搜索 credits：定位结果容器 + 排序文案 ----
        inp = page.locator('input[placeholder*="Search by keyword"]').first
        inp.scroll_into_view_if_needed()
        inp.fill("credits")
        page.wait_for_timeout(400)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        R["search_credits_ui"] = page.evaluate("""() => {
            const n = window.__norm;
            const body = n(document.body.textContent);
            // 找包含 results for 的容器
            const candidates = Array.from(document.querySelectorAll('div,section,p,h2,h3,span'))
                .filter(el => /results for/i.test(n(el.textContent)))
                .slice(0, 10)
                .map(el => ({tag: el.tagName.toLowerCase(), cls: el.className, text: n(el.textContent).slice(0,200)}));
            // 找 sorted 相关
            const sortedEls = Array.from(document.querySelectorAll('*')).filter(el => /Sorted by relevance/i.test(n(el.textContent)));
            return {
                has_sorted_text: /Sorted by relevance/i.test(body),
                sorted_hits: sortedEls.slice(0,5).map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, text:n(el.textContent).slice(0,120)})),
                results_containers: candidates,
            };
        }""")
        print("[SEARCH CREDITS UI]", json.dumps(R["search_credits_ui"], ensure_ascii=False))
        # 结果容器滚动性
        R["search_scroll"] = page.evaluate("""() => {
            const els = Array.from(document.querySelectorAll('*')).filter(el => {
                return el.scrollHeight > el.clientHeight + 5 && el.clientHeight > 100;
            }).slice(0, 10).map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, scrollH:el.scrollHeight, clientH:el.clientHeight}));
            return els;
        }""")
        print("[SEARCH SCROLL]", json.dumps(R["search_scroll"], ensure_ascii=False))
        page.screenshot(path=str(SHOTS / "05_search_credits_full.png"), full_page=True)

        # ---- 搜索空态结构 ----
        page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(6000)
        inp = page.locator('input[placeholder*="Search by keyword"]').first
        inp.scroll_into_view_if_needed()
        inp.fill("pokecut-unmatched-000")
        page.wait_for_timeout(400)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        R["search_empty_ui"] = page.evaluate("""() => {
            const n = window.__norm;
            const body = n(document.body.textContent);
            // 空态候选容器
            const cands = Array.from(document.querySelectorAll('div,section'))
                .filter(el => /No answer found/i.test(n(el.textContent)))
                .map(el => ({tag:el.tagName.toLowerCase(), cls:el.className, text:n(el.textContent).slice(0,300)}));
            const ticketBtn = Array.from(document.querySelectorAll('button,a')).find(el => /Submit a ticket/i.test(n(el.textContent)));
            return {
                no_answer_found: /No answer found/i.test(body),
                candidates: cands.slice(0,5),
                ticket_btn: ticketBtn ? {tag:ticketBtn.tagName.toLowerCase(), text:n(ticketBtn.textContent), cls:ticketBtn.className} : null,
            };
        }""")
        print("[SEARCH EMPTY UI]", json.dumps(R["search_empty_ui"], ensure_ascii=False))
        page.screenshot(path=str(SHOTS / "06_search_empty_full.png"), full_page=True)

        browser.close()

    (OUT / "explore_help_followup.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[DONE] saved explore_help_followup.json")

if __name__ == "__main__":
    main()
