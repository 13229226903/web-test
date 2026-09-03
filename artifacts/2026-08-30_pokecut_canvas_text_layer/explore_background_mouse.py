# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
OUT={"steps":[]}
def rec(name,**kw): OUT["steps"].append({"name":name,**kw}); print(json.dumps({"name":name,**kw},ensure_ascii=False)[:1800])
def snap(page,name): page.screenshot(path=str(SHOTS/f"{name}.png"))
def js(page,expr,arg=None): return page.evaluate(expr,arg)

def section_info(page):
    return js(page,"""() => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; const rr=row.getBoundingClientRect(); return {row:{x:rr.x,y:rr.y,w:rr.width,h:rr.height}, content_display: content?getComputedStyle(content).display:null};}}
      return null;
    }""")

def content_buttons(page):
    return js(page,"""() => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('button')].map((b,i)=>{const br=b.getBoundingClientRect(); return {i,cls:b.className,bg:b.style.backgroundColor||null,x:br.x,y:br.y,w:br.width,h:br.height};});}}}
      return null;
    }""")

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
    # scroll to Background and expand
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(800)
    before=section_info(page)
    row=before["row"]; page.mouse.click(row["x"]+row["w"]/2,row["y"]+row["h"]/2); page.wait_for_timeout(1000)
    after=section_info(page); snap(page,"108_background_expanded")
    rec("click_background_header",before=before,after=after)
    before_btns=content_buttons(page)
    # click no-fill (index 0)
    b=before_btns[0]; page.mouse.click(b["x"]+b["w"]/2,b["y"]+b["h"]/2); page.wait_for_timeout(1000)
    after_btns=content_buttons(page); snap(page,"109_background_no_fill")
    rec("click_background_no_fill", before=before_btns, after=after_btns)
    # click red
    before_btns=content_buttons(page)
    reds=[x for x in before_btns if x["bg"]=="rgb(174, 41, 42)"]
    if reds:
        r=reds[0]; page.mouse.click(r["x"]+r["w"]/2,r["y"]+r["h"]/2); page.wait_for_timeout(1000)
        after_btns=content_buttons(page); snap(page,"110_background_red")
        rec("click_background_red", before=before_btns, after=after_btns, clicked={"index":r["i"],"bg":r["bg"]})
    else:
        rec("click_background_red", clicked=None)
    browser.close()
(TASK/"background_interactions.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE")
