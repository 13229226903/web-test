# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time

TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
DAMAGED = r"D:\Test\web-test\test_images\损坏的图.png"
R3 = {}

def shot(name, full=False):
    try: page.screenshot(path=os.path.join(SHOTS, name), full_page=full)
    except Exception as e: print("shot fail", name, repr(e))

def home(wait=6000):
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(15000)
    home()

    # ---- FAQ collapse ----
    R3["faq"] = {}
    hdr = page.locator(".pk-collapse-header").first
    panel = hdr.locator("xpath=following-sibling::div[contains(@class,'pk-collapse-panel')]")
    before_h = panel.evaluate("el => el.getBoundingClientRect().height") if panel.count() else None
    R3["faq"]["before_panel_height"] = before_h
    hdr.click()
    page.wait_for_timeout(1200)
    after_h = panel.evaluate("el => el.getBoundingClientRect().height") if panel.count() else None
    R3["faq"]["after_panel_height"] = after_h
    R3["faq"]["header_html"] = hdr.evaluate("el => el.outerHTML.slice(0,1200)")
    R3["faq"]["panel_links"] = panel.locator("a").evaluate_all("els => els.map(e=>({t:(e.innerText||'').trim(), href:e.href, submit:e.getAttribute('data-submit-ticket')}))") if panel.count() else None
    shot("10_faq_expanded.png")
    hdr.click()
    page.wait_for_timeout(800)
    R3["faq"]["after_second_height"] = panel.evaluate("el => el.getBoundingClientRect().height") if panel.count() else None

    # ---- Enhance section inspection ----
    home()
    R3["enhance"] = {}
    enh = page.evaluate("""() => { const h=[...document.querySelectorAll('h2')].find(e=>e.innerText.includes('Enhance Photo Quality')); if(!h) return null; let s=h.closest('section')||h.parentElement; return s.outerHTML.slice(0,7000); }""")
    R3["enhance"]["section_html"] = enh
    # click via JS each tag button and record url
    R3["enhance"]["clicks"] = {}
    for nm in ["HD Enhance","Text Enhance","Portrait AI","Ultra Enhance"]:
        home()
        res = {}
        try:
            clicked = page.evaluate("""(nm) => { const b=[...document.querySelectorAll('button')].find(e=>(e.innerText||'').trim()===nm); if(b){ b.click(); return true; } return false; }""", nm)
            page.wait_for_timeout(2500)
            res = {"js_clicked": clicked, "url": page.url}
        except Exception as e:
            res = {"error": str(e)[:200]}
        R3["enhance"]["clicks"][nm] = res
        shot(f"16_enhance_{nm.replace(' ','_')}.png")

    # ---- Portrait scoped ----
    home()
    R3["portrait"] = {}
    R3["portrait"]["default_selected"] = page.evaluate("""() => { const tabs=[...document.querySelectorAll('[role=tab]')]; return tabs.map(t=>({t:(t.innerText||'').trim(), sel:t.getAttribute('aria-selected')})); }""")
    for tab in ["Face","Body","Hair","Background"]:
        home()
        try:
            page.get_by_role("tab", name=tab, exact=True).click()
            page.wait_for_timeout(1000)
            cards = page.evaluate("""() => { const h=[...document.querySelectorAll('h2')].find(e=>e.innerText.includes('Upgrade Portrait Details')); let s=h? (h.closest('section')||h.parentElement):null; if(!s) return []; return [...s.querySelectorAll('a')].filter(e=>e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0).map(e=>({t:(e.innerText||'').trim().replace(/\\n/g,' ').slice(0,60), href:e.href})); }""")
            R3["portrait"][tab] = cards[:20]
        except Exception as e:
            R3["portrait"][tab] = {"error": str(e)[:200]}

    # ---- Pricing nav (JS click) ----
    home()
    R3["bottom_nav"] = {}
    try:
        clicked = page.evaluate("""() => { const b=document.querySelector('nav.home-mobile-bottom-nav button[aria-label=Pricing]'); if(b){ b.click(); return true; } return false; }""")
        page.wait_for_timeout(4000)
        R3["bottom_nav"]["pricing_js_clicked"] = clicked
        R3["bottom_nav"]["pricing_url"] = page.url
    except Exception as e:
        R3["bottom_nav"]["pricing_error"] = str(e)[:200]

    # ---- Sign up inspection ----
    home()
    R3["signup"] = {}
    R3["signup"]["header_btn_html"] = page.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(e=>(e.innerText||'').trim()==='Sign up'); return b? b.outerHTML.slice(0,1500):null }""")
    try:
        page.get_by_role("button", name="Sign up").click()
        page.wait_for_timeout(3000)
        R3["signup"]["url_after_click"] = page.url
        # check for dialog/modal
        dlg = page.evaluate("""() => { const d=document.querySelector('[role=dialog], .modal, .popup, [class*=dialog]'); return d? {cls:d.className.slice(0,120), text:(d.innerText||'').slice(0,300)} : null }""")
        R3["signup"]["dialog"] = dlg
        shot("14_signup.png")
    except Exception as e:
        R3["signup"]["error"] = str(e)[:200]

    # ---- damaged upload error message ----
    home()
    R3["damaged"] = {}
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.locator("nav.home-mobile-bottom-nav").get_by_role("button", name="Upload").click()
        ch = fc.value
        ch.set_files([DAMAGED])
        page.wait_for_timeout(6000)
        R3["damaged"]["url"] = page.url
        # capture any toast/error element text
        R3["damaged"]["toasts"] = page.eval_on_selector_all("[class*='toast'], [class*='error'], [class*='message'], [role=alert]", "els => els.slice(0,10).map(e=>({cls:(e.className||'').slice(0,120), text:(e.innerText||'').trim().slice(0,200)}))")
        R3["damaged"]["body_head"] = page.inner_text("body")[:300]
    except Exception as e:
        R3["damaged"]["error"] = str(e)[:200]

    with open(os.path.join(TASK, "explore_fix2.json"), "w", encoding="utf-8") as f:
        json.dump(R3, f, ensure_ascii=False, indent=2)
    print("DONE3")
    print(json.dumps(R3, ensure_ascii=False, indent=2)[:9000])
    browser.close()
