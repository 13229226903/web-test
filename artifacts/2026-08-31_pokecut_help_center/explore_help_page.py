# -*- coding: utf-8 -*-
"""page-map-sync 探索脚本：Pokecut /help 帮助中心（对照 help 页优化需求文档 17 条 AC）。"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center")
SHOTS = OUT / "shots"
SHOTS.mkdir(exist_ok=True)

def norm(s):
    return " ".join((s or "").split())

def shot(page, name):
    p = SHOTS / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
    except Exception as e:
        print(f"[shot warn] {name}: {e}", file=sys.stderr)
    return str(p)

def js(page, expr):
    return page.evaluate(expr)

def vue_click(page, locator):
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    handle = locator.element_handle()
    if handle:
        handle.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
    page.wait_for_timeout(900)

def main():
    R = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        ctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
        page = ctx.new_page()
        page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(8000)

        R["url"] = page.url
        R["title"] = page.title()
        print("URL:", R["url"])
        print("TITLE:", R["title"])

        R["topnav"] = js(page, """() => {
            const n = window.__norm;
            const nav = document.querySelector('header, nav');
            if (!nav) return {found:false};
            const items = Array.from(nav.querySelectorAll('a,button')).map(a=>({text:n(a.textContent), href:a.getAttribute('href')||null})).filter(x=>x.text);
            return {found:true, items: items.slice(0,40)};
        }""")

        R["hero"] = js(page, """() => {
            const n = window.__norm;
            const inp = document.querySelector('input[placeholder*="Search by keyword"]');
            const q = (sel) => { const el = document.querySelector(sel); return el ? n(el.textContent) : null; };
            return {
                eyebrow: q('p[class*="eyebrow"]'),
                h1: q('h1'),
                desc: q('p[class*="Search guides for account"]'),
                search_placeholder: inp ? inp.getAttribute('placeholder') : null,
            };
        }""")

        R["popular_tags"] = js(page, """() => {
            const n = window.__norm;
            const tags = ['Credits','Subscription','Download','Batch','Project'];
            const btns = Array.from(document.querySelectorAll('button'));
            const out = [];
            for (const tag of tags) {
                const el = btns.find(b => { const t=n(b.textContent); return t === tag || t.startsWith(tag); });
                out.push({tag, found: !!el, text: el? n(el.textContent): null});
            }
            return out;
        }""")

        R["category_cards"] = js(page, """() => {
            const n = window.__norm;
            const cards = Array.from(document.querySelectorAll('button[class*="category-card"]'));
            return cards.map(c => ({text: n(c.textContent), cls: c.className}));
        }""")

        R["faq_nav"] = js(page, """() => {
            const n = window.__norm;
            const navs = Array.from(document.querySelectorAll('button[class*="faq-section__nav-item"]'));
            return navs.map(x => ({text: n(x.textContent), active: x.className.includes('active'), cls: x.className}));
        }""")

        R["faq_current"] = js(page, """() => {
            const n = window.__norm;
            const items = Array.from(document.querySelectorAll('article[class*="faq-item"]'));
            return items.map(it => {
                const q = it.querySelector('button[class*="question"]') || it.querySelector('button');
                const a = it.querySelector('div[class*="answer"]') || it.querySelector('div');
                return {question: q? n(q.textContent): null, answer: a? n(a.textContent): null, open: it.className.includes('open'), cls: it.className};
            });
        }""")

        R["bottom_cta"] = js(page, """() => {
            const n = window.__norm;
            const sec = document.querySelector('div[class*="support-cta"]');
            if (!sec) return {found:false};
            return {found:true, text: n(sec.textContent)};
        }""")

        shot(page, "01_desktop_initial")

        cats = ["Getting Started", "Account & Access", "Plans, Credits & Billing",
                "AI Tools & Editing", "Batch, Download & Projects", "Commercial, Safety & Support"]
        R["categories"] = {}
        for cat in cats:
            try:
                nav = page.locator(f"button[class*='faq-section__nav-item']:has-text('{cat}')").first
                vue_click(page, nav)
                page.wait_for_timeout(800)
                data = js(page, """() => {
                    const n = window.__norm;
                    const items = Array.from(document.querySelectorAll('article[class*="faq-item"]'));
                    const list = items.map(it => {
                        const q = it.querySelector('button[class*="question"]') || it.querySelector('button');
                        const a = it.querySelector('div[class*="answer"]') || it.querySelector('div');
                        return {question: q? n(q.textContent): null, answer: a? n(a.textContent): null, open: it.className.includes('open')};
                    });
                    return {questions: list.map(x=>({question:x.question, open:x.open})), firstAnswer: list[0]? list[0].answer : null, openCount: list.filter(x=>x.open).length, firstOpen: list[0]? list[0].open : null};
                }""")
                R["categories"][cat] = data
                shot(page, f"02_cat_{cat.replace(' ','_').replace(',','').replace('&','and')}")
                print(f"[CAT] {cat}: {len(data.get('questions',[]))} questions, open={data.get('openCount')}, firstOpen={data.get('firstOpen')}")
            except Exception as e:
                R["categories"][cat] = {"error": str(e)}
                print(f"[CAT ERROR] {cat}: {e}")

        # FAQ 展开/收起 + 同类只保留一条（在 Getting Started 分类上做）
        R["faq_accordion"] = {}
        try:
            page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(6000)
            gs = page.locator("button[class*='faq-section__nav-item']:has-text('Getting Started')").first
            vue_click(page, gs)
            page.wait_for_timeout(800)
            items = page.locator("article[class*='faq-item']")
            count = items.count()
            R["faq_accordion"]["item_count"] = count
            if count >= 2:
                # 点第一条
                q0 = items.nth(0).locator("button[class*='question']")
                vue_click(page, q0)
                page.wait_for_timeout(500)
                # 点第二条
                q1 = items.nth(1).locator("button[class*='question']")
                vue_click(page, q1)
                page.wait_for_timeout(500)
                st = js(page, """() => {
                    const items = Array.from(document.querySelectorAll('article[class*="faq-item"]'));
                    return items.map(it => ({open: it.className.includes('open'), q: window.__norm(it.querySelector('button[class*="question"]')?.textContent)}));
                }""")
                R["faq_accordion"]["after_click_1st_then_2nd"] = st
                print("[FAQ] after click 1st then 2nd:", json.dumps(st, ensure_ascii=False))
                # 再点第二条收起
                vue_click(page, q1)
                page.wait_for_timeout(500)
                st2 = js(page, """() => {
                    const items = Array.from(document.querySelectorAll('article[class*="faq-item"]'));
                    return items.map(it => ({open: it.className.includes('open'), q: window.__norm(it.querySelector('button[class*="question"]')?.textContent)}));
                }""")
                R["faq_accordion"]["after_collapse"] = st2
                print("[FAQ] after collapse 2nd:", json.dumps(st2, ensure_ascii=False))
                shot(page, "02b_faq_accordion")
        except Exception as e:
            R["faq_accordion"]["error"] = str(e)
            print("[FAQ ACCORDION ERROR]", e)

        # 搜索
        R["search"] = {}
        for kw in ["credits", "pokecut-unmatched-000"]:
            try:
                page.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(6000)
                inp = page.locator('input[placeholder*="Search by keyword"]').first
                inp.scroll_into_view_if_needed()
                inp.fill(kw)
                page.wait_for_timeout(400)
                page.keyboard.press("Enter")
                page.wait_for_timeout(2500)
                data = js(page, """() => {
                    const n = window.__norm;
                    const body = n(document.body.textContent);
                    const m = body.match(/(\\d+)\\s+results?\\s+for/);
                    const resultBlocks = Array.from(document.querySelectorAll('article, li, [class*="result"], [class*="search-result"]'))
                        .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 20 && n(el.textContent).length > 10; })
                        .slice(0, 25)
                        .map(el => n(el.textContent).slice(0, 200));
                    return {
                        url: location.href,
                        has_results_for: /results? for/i.test(body),
                        results_count_text: m ? m[0] : null,
                        has_sorted_by_relevance: /Sorted by relevance/i.test(body),
                        has_no_answer_found: /No answer found/i.test(body),
                        has_submit_ticket: /Submit a ticket/i.test(body),
                        result_blocks: resultBlocks,
                    };
                }""")
                R["search"][kw] = data
                shot(page, f"03_search_{kw}")
                print(f"[SEARCH] {kw}: count_text={data['results_count_text']}, sorted={data['has_sorted_by_relevance']}, no_answer={data['has_no_answer_found']}, submit_ticket={data['has_submit_ticket']}")
            except Exception as e:
                R["search"][kw] = {"error": str(e)}
                print(f"[SEARCH ERROR] {kw}: {e}")

        # 顶部 Contact us 入口
        R["topnav_contact"] = {}
        try:
            page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(6000)
            navinfo = js(page, """() => {
                const n = window.__norm;
                const nav = document.querySelector('header, nav');
                if (!nav) return {found:false};
                const items = Array.from(nav.querySelectorAll('a,button')).map(a=>({text:n(a.textContent), href:a.getAttribute('href')||null})).filter(x=>x.text);
                const contact = items.find(x=>/Contact us/i.test(x.text));
                return {found: !!contact, contact, items: items.slice(0,40)};
            }""")
            R["topnav_contact"] = navinfo
            print(f"[TOPNAV] Contact us found on home: {navinfo.get('found')}")
        except Exception as e:
            R["topnav_contact"] = {"error": str(e)}
            print(f"[TOPNAV ERROR] {e}")

        # 移动端
        R["mobile"] = {}
        try:
            mctx = browser.new_context(viewport={"width": 375, "height": 812}, locale="en-US")
            mctx.add_init_script("window.__norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();")
            mp = mctx.new_page()
            mp.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
            mp.wait_for_timeout(8000)
            mob = js(mp, """() => {
                const cards = Array.from(document.querySelectorAll('button[class*="category-card"]'));
                const grid = document.querySelector('div[class*="category-section"] div[class*="grid"], div[class*="category-section__grid"]');
                const leftnav = document.querySelector('button[class*="faq-section__nav-item"]');
                const faqItems = Array.from(document.querySelectorAll('article[class*="faq-item"]'));
                const gs = grid ? getComputedStyle(grid) : null;
                return {
                    url: location.href,
                    cardCount: cards.length,
                    gridColumns: gs ? gs.gridTemplateColumns : null,
                    hasLeftNavVisible: !!leftnav && leftnav.getBoundingClientRect().width > 0,
                    faqItemCount: faqItems.length,
                    bodyOverflowX: document.body.scrollWidth > window.innerWidth,
                };
            }""")
            shot(mp, "04_mobile_initial")
            R["mobile"]["initial"] = mob
            print(f"[MOBILE] cards={mob['cardCount']}, gridCols={mob['gridColumns']}, hasLeftNav={mob['hasLeftNavVisible']}, overflowX={mob['bodyOverflowX']}")
            mctx.close()
        except Exception as e:
            R["mobile"] = {"error": str(e)}
            print(f"[MOBILE ERROR] {e}")

        browser.close()

    (OUT / "explore_help_page.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[DONE] saved explore_help_page.json")

if __name__ == "__main__":
    main()
