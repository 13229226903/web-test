# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
OUT={"steps":[]}
def rec(name,**kw): OUT["steps"].append({"name":name,**kw}); print(json.dumps({"name":name,**kw},ensure_ascii=False)[:2000])
def snap(page,name): page.screenshot(path=str(SHOTS/f"{name}.png"))
def js(page,expr,arg=None): return page.evaluate(expr,arg)

def space_sliders(page):
    return js(page,"""() => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Space');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('input.space-slider')].map(s=>({value:s.value,min:s.min,max:s.max,disabled:s.disabled}));}}}
      return null;
    }""")
def dimension_text(page):
    return js(page,"""() => {
      const els=[...document.querySelectorAll('div,span')];
      for(const el of els){const t=(el.textContent||'').trim(); const m=t.match(/^(\\d+)\\s*x\\s*(\\d+)$/); const r=el.getBoundingClientRect(); if(m&&r.width>0&&r.height>0&&r.x>=1000&&r.x<=1560&&r.y>=430&&r.y<=520) return t;}
      return null;
    }""")
def set_height(page,val):
    return js(page,"""(val) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Space');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const ss=[...content.querySelectorAll('input.space-slider')]; if(ss[1]){const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; set.call(ss[1],String(val)); ss[1].dispatchEvent(new Event('input',{bubbles:true})); ss[1].dispatchEvent(new Event('change',{bubbles:true})); return {value:ss[1].value,disabled:ss[1].disabled};}}}} return null;
    }""",val)

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
    # edit two lines
    page.mouse.dblclick(900,500); page.wait_for_timeout(1200)
    ta=page.locator("textarea.fixed.h-px.w-px").first
    ta.fill("line1\nline2"); page.wait_for_timeout(1000); page.keyboard.press("Escape"); page.wait_for_timeout(1000)
    # reopen panel via toolbar Adjust
    locs=page.locator("button", has_text="Adjust").all()
    for b in locs:
        r=b.bounding_box()
        if r and r['y']<440:
            page.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2); break
    page.wait_for_timeout(1200)
    # open Space section
    locs=page.locator("button", has_text="Space").all()
    for b in locs:
        r=b.bounding_box()
        if r and r['y']>480 and r['x']>=1000:
            page.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2); break
    page.wait_for_timeout(1000)
    before=space_sliders(page); dim_before=dimension_text(page); snap(page,"122_space_two_lines_before")
    set_height(page,50); page.wait_for_timeout(1500)
    after=space_sliders(page); dim_after=dimension_text(page); snap(page,"123_space_height_50")
    rec("two_lines_space_height", before=before, after=after, dimension_before=dim_before, dimension_after=dim_after)
    browser.close()
(TASK/"space_height_two_lines.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE")
