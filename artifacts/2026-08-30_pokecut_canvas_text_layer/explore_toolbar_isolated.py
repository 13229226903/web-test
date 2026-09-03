# -*- coding: utf-8 -*-
"""Toolbar buttons isolated observation (fresh panel state each button)."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"
SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
OUT={"steps":[]}
def rec(name,**kw):
    item={"name":name,**kw}; OUT["steps"].append(item); print(json.dumps(item,ensure_ascii=False)[:600])
def snap(page,name):
    path=SHOTS/f"{name}.png"; page.screenshot(path=str(path)); return path

def visible_buttons(page):
    return page.evaluate("""() => { const out=[]; document.querySelectorAll('button').forEach(b=>{const r=b.getBoundingClientRect(); const t=(b.textContent||'').trim().replace(/\\s+/g,' '); if(r.width>0&&r.height>0&&t) out.push({text:t.slice(0,50),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}); return out; }""")
def findb(page,txt, ymin=400,ymax=450):
    return page.evaluate("""(opts)=>{const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()===opts.txt); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>0&&r.height>0&&r.y>=opts.ymin&&r.y<=opts.ymax)return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),txt:opts.txt,w:Math.round(r.width),h:Math.round(r.height)};} return null;}""", {"txt":txt,"ymin":ymin,"ymax":ymax})
def panel_visible(page):
    return page.evaluate("""() => { const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic'); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>100&&r.height>30&&r.y>400)return true;} return false; }""")
def click_pt(page,d):
    page.mouse.click(d['x'],d['y'])

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
    def ensure_panel():
        if not panel_visible(page):
            d=findb(page,"Adjust")
            if d: click_pt(page,d); page.wait_for_timeout(1000)
        return panel_visible(page)
    # baseline
    snap(page,"30_baseline_text_selected")
    rec("baseline", panel=panel_visible(page), toolbar=[d for d in visible_buttons(page) if 400<=d['y']<=450 and d['x']<1400])
    buttons=["Adjust","Move Up","Move Down","To Top","To Bottom","Flip h","Flip v","Rotation","Delete"]
    revert_map={"Move Up":"Move Down","Move Down":"Move Up","To Top":"To Bottom","To Bottom":"To Top","Flip h":"Flip h","Flip v":"Flip v"}
    for t in buttons:
        ensure_panel()
        d=findb(page,t)
        if not d:
            rec("missing",text=t); continue
        before=panel_visible(page)
        click_pt(page,d); page.wait_for_timeout(1200)
        after=panel_visible(page)
        snap(page, f"31_{t.replace(' ','_').lower()}_clicked")
        rec(f"click_{t.replace(' ','_').lower()}", before_panel=before, after_panel=after, button=d, body=page.locator("body").inner_text()[:250].replace("\n"," | "))
        # Revert if reversible
        if t in revert_map:
            rt=revert_map[t]
            rd=findb(page,rt)
            if rd:
                click_pt(page,rd); page.wait_for_timeout(1000)
        # For Delete, re-add text so next iterations have a selected text layer
        if t=="Delete":
            page.locator("button[data-tool-id='text']").first.click(); page.wait_for_timeout(1500)
        # Ensure panel open for next (except after Delete handled)
        if t!="Delete":
            ensure_panel()
    browser.close()
(TASK/"explore_toolbar_isolated.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE")
