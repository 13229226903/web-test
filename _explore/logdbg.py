# -*- coding: utf-8 -*-
"""逐步登录调试：截图 + 转储每步的 button/input 状态。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import BASE, EMAIL, CODE, DEBUG, log, dismiss
from playwright.sync_api import sync_playwright


def dump(page, tag):
    info = page.evaluate("""() => {
        const vis = el => { const r=el.getBoundingClientRect(); const s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'; };
        const btns=[], ins=[];
        document.querySelectorAll('button').forEach(b=>{if(vis(b)){const r=b.getBoundingClientRect();
            btns.push(((b.innerText||'').trim().slice(0,30))+` @${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`);}});
        document.querySelectorAll('input').forEach(i=>{if(vis(i)){const r=i.getBoundingClientRect();
            ins.push(`${i.type} ph=${i.placeholder} @${Math.round(r.x)},${Math.round(r.y)}`);}});
        return {btns, ins, url:location.href, bodylen:document.body.innerText.length,
                bodyhead:document.body.innerText.slice(0,120)};
    }""")
    log(f"[{tag}] url={info['url']}")
    log(f"[{tag}] inputs:", info["ins"])
    log(f"[{tag}] buttons:", info["btns"][:25])
    page.screenshot(path=os.path.join(DEBUG, f"logdbg_{tag}.png"))


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page = ctx.new_page()
    page.goto(BASE); page.wait_for_timeout(6000)
    dump(page, "1_home")
    # 点 Log in
    try:
        page.get_by_text("Log in", exact=True).first.click(timeout=8000)
    except Exception as e:
        log("click Log in err:", e)
    page.wait_for_timeout(3000)
    dump(page, "2_after_login_click")
    allin = page.evaluate("() => [...document.querySelectorAll('input')].map(i=>i.type+':'+(i.placeholder||''))")
    log("ALL inputs (any vis):", allin)
    log("BODY after click:", page.locator("body").inner_text().replace("\n"," ")[:300])
    browser.close()
