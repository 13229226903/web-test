# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time
TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
R4 = {}

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

    # Portrait: JS click each tab and capture selected + scoped card links
    R4["portrait"] = {}
    for tab in ["Face","Body","Hair","Background"]:
        home()
        # JS click
        page.evaluate("""(nm) => { const t=[...document.querySelectorAll('[role=tab]')].find(e=>(e.innerText||'').trim()===nm); if(t) t.click(); }""", tab)
        page.wait_for_timeout(1200)
        R4["portrait"][tab] = page.evaluate("""() => {
          const tabs=[...document.querySelectorAll('[role=tab]')].map(t=>({t:(t.innerText||'').trim(), sel:t.getAttribute('aria-selected')}));
          const h=[...document.querySelectorAll('h2')].find(e=>e.innerText.includes('Upgrade Portrait Details'));
          let s=h? (h.closest('section')||h.parentElement):null;
          const links = s? [...s.querySelectorAll('a')].filter(e=>e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0).map(e=>({t:(e.innerText||'').trim().replace(/\\n/g,' ').slice(0,60), href:e.getAttribute('href')})) : [];
          return {tabs, links:links.slice(0,20)};
        }""")

    # Sign up deeper check
    home()
    R4["signup"] = {}
    try:
        page.get_by_role("button", name="Sign up").click()
        page.wait_for_timeout(5000)
        R4["signup"]["url"] = page.url
        R4["signup"]["inputs"] = page.eval_on_selector_all("input", "els => els.slice(0,10).map(e=>({type:e.type, ph:e.getAttribute('placeholder'), aria:e.getAttribute('aria-label')}))")
        R4["signup"]["dialogs"] = page.eval_on_selector_all("[role=dialog], .el-dialog, .modal, .popup, [class*='login'], [class*='Login'], [class*='signup'], [class*='Signup']", "els => els.slice(0,10).map(e=>({cls:(e.className||'').slice(0,120), text:(e.innerText||'').trim().slice(0,200)}))")
        R4["signup"]["body_tail"] = page.inner_text("body")[:600]
        page.screenshot(path=os.path.join(SHOTS,"14b_signup_after.png"))
    except Exception as e:
        R4["signup"]["error"] = str(e)[:200]

    # Reviews scoped images
    home()
    R4["reviews"] = page.evaluate("""() => {
      const h=[...document.querySelectorAll('h2')].find(e=>e.innerText.includes('What Users Say'));
      let s=h? (h.closest('section')||h.parentElement):null;
      if(!s) return {imgs:[]};
      const imgs=[...s.querySelectorAll('img')].map(e=>({src:e.src.split('/').pop(), alt:e.alt||''}));
      const names=[...s.querySelectorAll('a[href*=producthunt]')].map(e=>({t:(e.innerText||'').trim(), href:e.href}));
      return {imgs, names:names.slice(0,20)};
    }""")

    # Function board section heading/cards check
    home()
    R4["function_board_html"] = page.evaluate("""() => { const h=[...document.querySelectorAll('h2')].find(e=>e.innerText.includes('AI Templates')); return null; }""")

    with open(os.path.join(TASK, "explore_fix3.json"), "w", encoding="utf-8") as f:
        json.dump(R4, f, ensure_ascii=False, indent=2)
    print("DONE4")
    print(json.dumps(R4, ensure_ascii=False, indent=2)[:9000])
    browser.close()
