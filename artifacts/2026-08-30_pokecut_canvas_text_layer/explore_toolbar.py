# -*- coding: utf-8 -*-
"""Canvas text feature full-flow exploration - toolbar phase."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"
SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
OUT={"task":"2026-08-30_pokecut_canvas_text_layer","steps":[]}

def rec(name, **kw):
    item={"name":name, **kw}; OUT["steps"].append(item); print(json.dumps(item,ensure_ascii=False)[:800])
def snap(page,name):
    path=SHOTS/f"{name}.png"; page.screenshot(path=str(path)); return str(path)

def visible_buttons(page):
    return page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('button').forEach(b=>{
        const r=b.getBoundingClientRect();
        const t=(b.textContent||'').trim().replace(/\\s+/g,' ');
        if(r.width>0 && r.height>0 && t) out.push({text:t.slice(0,60), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
      });
      return out;
    }""")

def find_button(page, text, y_min=None, y_max=None, x_min=None, x_max=None):
    for d in visible_buttons(page):
        t=d['text']
        if t.lower()!=text.lower(): continue
        if y_min is not None and d['y']<y_min: continue
        if y_max is not None and d['y']>y_max: continue
        if x_min is not None and d['x']<x_min: continue
        if x_max is not None and d['x']>x_max: continue
        return d
    return None

def click_center(page,d):
    page.mouse.click(d['x']+d['w']/2, d['y']+d['h']/2)

def panel_visible(page):
    return page.evaluate("""() => {
      const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic');
      for(const b of bs){ const r=b.getBoundingClientRect(); if(r.width>100 && r.height>30 && r.y>400) return true; }
      return false;
    }""")

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    rec("00_create_loaded", url=page.url)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc:
        card.click()
    fc.value.set_files(str(ROOT/"test_images"/"低分辨率.JPG"))
    page.wait_for_timeout(12000)
    snap(page,"10_canvas_loaded")
    rec("10_canvas_loaded", url=page.url)
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)
    snap(page,"11_after_add_text")
    initial_buttons=visible_buttons(page)
    toolbar=[d for d in initial_buttons if 400<=d['y']<=440 and d['x']<1400]
    rec("11_after_add_text", panel_visible=panel_visible(page), toolbar=toolbar)
    toolbar_texts=["Adjust","Move Up","Move Down","To Top","To Bottom","Flip h","Flip v","Rotation","Delete"]
    for t in toolbar_texts:
        d=find_button(page,t,y_min=400,y_max=445,x_min=500,x_max=1400)
        if not d:
            rec("toolbar_missing", text=t); continue
        before=panel_visible(page)
        click_center(page,d)
        page.wait_for_timeout(1200)
        after=panel_visible(page)
        snap(page, f"20_toolbar_{t.replace(' ','_').lower()}")
        body=page.locator("body").inner_text()
        rec(f"toolbar_{t.replace(' ','_').lower()}_clicked", before_panel=before, after_panel=after,
            button=d, body_snippet=body[:300].replace("\n"," | "))
        if t=="Move Up":
            d2=find_button(page,"Move Down",y_min=400,y_max=445)
            if d2: click_center(page,d2); page.wait_for_timeout(800)
        elif t=="Move Down":
            d2=find_button(page,"Move Up",y_min=400,y_max=445)
            if d2: click_center(page,d2); page.wait_for_timeout(800)
        elif t=="To Top":
            d2=find_button(page,"To Bottom",y_min=400,y_max=445)
            if d2: click_center(page,d2); page.wait_for_timeout(800)
        elif t=="To Bottom":
            d2=find_button(page,"To Top",y_min=400,y_max=445)
            if d2: click_center(page,d2); page.wait_for_timeout(800)
        elif t in ("Flip h","Flip v"):
            click_center(page,d); page.wait_for_timeout(800)
        elif t=="Rotation":
            page.keyboard.press("Escape"); page.wait_for_timeout(500)
            page.mouse.click(900,300); page.wait_for_timeout(500)
            page.locator("button[data-tool-id='text']").first.click(); page.wait_for_timeout(1000)
        elif t=="Adjust":
            pass
        elif t=="Delete":
            page.locator("button[data-tool-id='text']").first.click(); page.wait_for_timeout(1500)
    final_buttons=visible_buttons(page)
    snap(page,"29_toolbar_after_explore")
    rec("29_toolbar_after_explore", panel_visible=panel_visible(page), toolbar=[d for d in final_buttons if 400<=d['y']<=440 and d['x']<1400])
    browser.close()

(TASK/"explore_toolbar.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE", TASK/"explore_toolbar.json")
