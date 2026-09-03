# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-29_pokecut_canvas_photo_enhancer"; SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
out={"steps":[]}
def rec(page,name,extra=None):
    out["steps"].append({"name":name,"url":page.url,"extra":extra or {}}); print(name, extra or {})
def snap(page,name):
    p=SHOTS/f"{name}.png"; page.screenshot(path=str(p)); return str(p)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1500)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc_info:
        card.click()
    fc=fc_info.value; fc.set_files(str(ROOT/"test_images"/"文字测例.jpg"))
    page.wait_for_timeout(15000)
    page.locator("button.toolbar-hover-button", has_text="Enhance").first.click()
    page.wait_for_timeout(4000)
    snap(page,"20_enhance_standard")
    # inspect AI Enhancer panel outerHTML / buttons
    panel = page.locator("body").locator("div", has_text="AI Enhancer").last
    print("panel count", page.locator("div", has_text="AI Enhancer").count())
    # list buttons inside panel
    texts = page.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('button, [role=button], [data-mode], [data-tab]'));
      return els.map((e,i)=> { const r=e.getBoundingClientRect(); return {i, tag:e.tagName, text:(e.innerText||'').trim().replace(/\\n/g,' | ').slice(0,120), cls:e.className, data: Object.fromEntries([...e.attributes].filter(a=>a.name.startsWith('data-')).map(a=>[a.name,a.value])), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)}; }).filter(x=>x.text && x.w>0 && x.h>0);
    }""")
    print(json.dumps(texts, ensure_ascii=False, indent=2))
    # click Text Mode
    for name in ["Text Mode"]:
        loc=page.get_by_text(name, exact=True)
        print(name, "count", loc.count())
        if loc.count():
            # maybe nested span; click last visible
            loc.last.click()
            page.wait_for_timeout(3000)
            snap(page,"21_after_text_mode")
            body=page.locator("body").inner_text()
            rec(page,"21_after_text_mode",{"body_tail":body[-2500:]})
            print("BODY TAIL", body[-3000:])
    b.close()
(TASK/"explore_enhance_text_mode.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
