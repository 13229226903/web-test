# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc:
        card.click()
    fc.value.set_files(str(ROOT/"test_images"/"低分辨率.JPG"))
    page.wait_for_timeout(12000)
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)
    # switch to Basic tab with mouse click
    def click_tab_mouse(txt):
        loc=page.locator("button", has_text=txt).all()
        for b in loc:
            try:
                r=b.bounding_box()
                if r and r['y']>430 and r['y']<500:
                    page.mouse.click(r['x']+r['width']/2, r['y']+r['height']/2); page.wait_for_timeout(1000); return r
            except: pass
        return None
    print('basic tab', click_tab_mouse('Basic'))
    # Font mouse click
    loc=page.locator("button", has_text="Font").all()
    for b in loc:
        try:
            r=b.bounding_box()
            if r and r['y']>550 and r['x']>1080:
                print('font box', r)
                page.mouse.click(r['x']+r['width']/2, r['y']+r['height']/2)
                break
        except: pass
    page.wait_for_timeout(2000)
    page.screenshot(path=str(SHOTS/'61_font_mouse_open.png'))
    # dump visible texts around panel and maybe entire page
    txt=page.evaluate("""() => { const out=[]; document.querySelectorAll('button,span,p,div,li').forEach(el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el); if(r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&r.y>430&&r.y<900){let t=(el.textContent||'').trim().replace(/\\s+/g,' '); if(t&&t.length<80) out.push({tag:el.tagName,text:t,x:Math.round(r.x),y:Math.round(r.y)});}}); const seen=new Set(); const res=[]; for(const o of out){const k=o.tag+'|'+o.text+'|'+o.x+'|'+o.y; if(!seen.has(k)){seen.add(k);res.push(o);}} return res; }""")
    for d in txt: print(json.dumps(d,ensure_ascii=False))
    browser.close()
