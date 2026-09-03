# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time

TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
DAMAGED = r"D:\Test\web-test\test_images\损坏的图.png"
R2 = {}

def shot(name, full=False):
    try: page.screenshot(path=os.path.join(SHOTS, name), full_page=full)
    except Exception as e: print("shot fail", name, repr(e))

def home(wait=6000):
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait)

def links_visible():
    return page.eval_on_selector_all("a", """els => els.filter(e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.width>0 && r.height>0 && cs.visibility!=='hidden' && cs.display!=='none';}).map(e=>({t:(e.innerText||'').trim().replace(/\\n/g,' ').slice(0,80), href:e.href, target:e.target||'', rel:e.rel||''}))""")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(15000)
    home()

    # ---- Portrait tabs via role=tab ----
    R2["portrait_tabs"] = []
    for tab in ["Face","Body","Hair","Background"]:
        home()
        try:
            tb = page.get_by_role("tab", name=tab, exact=True)
            cnt = tb.count()
            if cnt:
                tb.first.click()
                page.wait_for_timeout(1000)
                active = page.evaluate("""() => { const bs=[...document.querySelectorAll('[role=tab]')]; const b=bs.find(e=>(e.innerText||'').trim()==='%s'); return b? {cls:b.className, aria_selected:b.getAttribute('aria-selected')} : null; }""" % tab)
                cards = [l for l in links_visible() if ('image-to-image-ai' in l['href'] or 'body-editor' in l['href'] or 'hair' in l['href'] or 'background' in l['href'])]
                R2["portrait_tabs"].append({"tab": tab, "count": cnt, "active": active, "card_links": cards[:20]})
            else:
                R2["portrait_tabs"].append({"tab": tab, "count": 0})
        except Exception as e:
            R2["portrait_tabs"].append({"tab": tab, "error": str(e)[:200]})

    # ---- Effect templates: first template 'Butt' ----
    home()
    R2["effect_template"] = {}
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_role("button", name="Butt").first.click()
        ch = fc.value
        R2["effect_template"]["chooser"] = True
        ch.set_files([IMG])
        page.wait_for_timeout(6000)
        R2["effect_template"]["upload_url"] = page.url
        shot("05_effect_template_canvas.png")
    except Exception as e:
        R2["effect_template"]["chooser"] = False
        R2["effect_template"]["error"] = str(e)[:250]

    # ---- Enhance board: HD Enhance / Text Enhance / Portrait AI / Ultra Enhance ----
    home()
    R2["enhance"] = {}
    for nm in ["HD Enhance","Text Enhance"]:
        home()
        try:
            page.get_by_role("button", name=nm).first.click()
            page.wait_for_timeout(4000)
            R2["enhance"][nm] = {"url": page.url}
        except Exception as e:
            R2["enhance"][nm] = {"error": str(e)[:200]}
    for nm in ["Portrait AI","Ultra Enhance"]:
        home()
        res = {}
        fc_event = {"triggered": False}
        def on_fc(chooser):
            fc_event["triggered"] = True
            try: chooser.set_files([])
            except Exception: pass
        page.on("filechooser", on_fc)
        try:
            page.get_by_role("button", name=nm).first.click()
            page.wait_for_timeout(3000)
        except Exception as e:
            res["click_error"] = str(e)[:200]
        page.remove_listener("filechooser", on_fc)
        res["filechooser_event"] = fc_event["triggered"]
        res["url_after_click"] = page.url
        R2["enhance"][nm] = res

    # ---- FAQ expand/collapse + structure ----
    home()
    R2["faq"] = {}
    faq_html = page.evaluate("""() => { const h=[...document.querySelectorAll('h2')].find(e=>e.innerText.includes('Frequently Asked Questions')); if(!h) return null; let s=h.closest('section'); if(!s) s=h.parentElement; return s.outerHTML.slice(0,6000); }""")
    R2["faq"]["section_html"] = faq_html
    # find clickable question (button or h3) for first Q
    first_click = page.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(e=>e.innerText.includes('What is Pokecut')); if(!h) return {ok:false}; let t=h.closest('button')||h; t.click(); return {ok:true, tag:t.tagName}; }""")
    page.wait_for_timeout(1200)
    R2["faq"]["first_click"] = first_click
    R2["faq"]["answer_visible_after_click"] = page.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(e=>e.innerText.includes('What is Pokecut')); if(!h) return null; let c=h.closest('button')||h; let panel=document.querySelector('[data-testid]') ; let next = c.nextElementSibling; return {next: next? next.innerText.slice(0,300):null, expanded: c.getAttribute('aria-expanded')}; }""")
    shot("10_faq_expanded.png")
    # collapse by clicking again
    page.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(e=>e.innerText.includes('What is Pokecut')); if(h){ let t=h.closest('button')||h; t.click(); } }""")
    page.wait_for_timeout(800)
    R2["faq"]["after_second_click"] = page.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(e=>e.innerText.includes('What is Pokecut')); if(!h) return null; let c=h.closest('button')||h; return {expanded: c.getAttribute('aria-expanded')}; }""")

    # ---- Mobile app alignment ----
    home()
    R2["mobile_app"] = page.evaluate("""() => { const t=document.body.innerText; const i=t.indexOf('Pokecut Mobile App'); if(i<0) return null; const nodes=[...document.querySelectorAll('h2,h3,p,div')].filter(e=>(e.innerText||'').includes('Pokecut Mobile App') && e.innerText.length<200); const n=nodes[0]; let sec=n? (n.closest('section')||n.parentElement):null; function info(el){ if(!el) return null; const cs=getComputedStyle(el); return {tag:el.tagName, text:(el.innerText||'').trim().slice(0,120), textAlign:cs.textAlign, direction:cs.direction, display:cs.display}; } return {sec: sec? sec.outerHTML.slice(0,2500):null, nodes:nodes.slice(0,6).map(info)}; }""")

    # ---- Bottom nav fixed: Upload / Pricing / damaged ----
    home()
    R2["bottom_nav"] = {}
    nav = page.locator("nav.home-mobile-bottom-nav")
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            nav.get_by_role("button", name="Upload").click()
        ch = fc.value
        R2["bottom_nav"]["upload_chooser"] = True
        ch.set_files([IMG])
        page.wait_for_timeout(6000)
        R2["bottom_nav"]["upload_url"] = page.url
        shot("12_upload_canvas.png")
    except Exception as e:
        R2["bottom_nav"]["upload_chooser"] = {"triggered": False, "error": str(e)[:250]}
    home()
    try:
        nav = page.locator("nav.home-mobile-bottom-nav")
        nav.get_by_role("button", name="Pricing").click()
        page.wait_for_timeout(4000)
        R2["bottom_nav"]["pricing_url"] = page.url
    except Exception as e:
        R2["bottom_nav"]["pricing_error"] = str(e)[:250]
    # damaged image upload via Upload
    home()
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.locator("nav.home-mobile-bottom-nav").get_by_role("button", name="Upload").click()
        ch = fc.value
        ch.set_files([DAMAGED])
        page.wait_for_timeout(6000)
        R2["bottom_nav"]["damaged_upload_url"] = page.url
        R2["bottom_nav"]["damaged_upload_body"] = page.inner_text("body")[:400]
    except Exception as e:
        R2["bottom_nav"]["damaged_upload_error"] = str(e)[:250]

    # ---- Sign up header ----
    home()
    try:
        page.get_by_role("button", name="Sign up").click()
        page.wait_for_timeout(2500)
        R2["signup"] = {"url": page.url, "modal_text": page.inner_text("body")[:300]}
        shot("14_signup.png")
    except Exception as e:
        R2["signup"] = {"error": str(e)[:200]}

    # ---- Language button ----
    home()
    try:
        page.locator("button", has_text="Language").first.click()
        page.wait_for_timeout(2000)
        R2["language"] = {"clicked": True, "body_text": page.inner_text("body")[:500]}
        shot("15_language.png")
    except Exception as e:
        R2["language"] = {"error": str(e)[:200]}

    with open(os.path.join(TASK, "explore_fix.json"), "w", encoding="utf-8") as f:
        json.dump(R2, f, ensure_ascii=False, indent=2)
    print("DONE2")
    print(json.dumps(R2, ensure_ascii=False, indent=2)[:8000])
    browser.close()
