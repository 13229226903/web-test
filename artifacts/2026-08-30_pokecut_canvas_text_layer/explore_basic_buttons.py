# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
OUT={"steps":[]}
def rec(name,before=None,after=None,**kw):
    item={"name":name}
    if before is not None: item["before"]=before
    if after is not None: item["after"]=after
    item.update(kw); OUT["steps"].append(item); print(json.dumps(item,ensure_ascii=False)[:2200])
def snap(page,name): page.screenshot(path=str(SHOTS/f"{name}.png"))
def js(page,expr,arg=None): return page.evaluate(expr,arg)

def alignment_buttons(page):
    return js(page,"""() => {
      const ps=[...document.querySelectorAll('p')].filter(p=>p.textContent.trim()==='Alignment');
      for(const p of ps){const r=p.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const box=p.parentElement; if(box){const bs=[...box.querySelectorAll('button')]; return bs.map((b,i)=>{const br=b.getBoundingClientRect(); return {i,cls:b.className,x:br.x,y:br.y,w:br.width,h:br.height};});}}}
      return null;
    }""")

def click_font_button(page):
    return js(page,"""() => {
      const bs=[...document.querySelectorAll('button')].filter(b=>(b.textContent||'').trim()==='Font');
      for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>0&&r.x>=1000&&r.y>500&&r.y<700){return {x:r.x,y:r.y,w:r.width,h:r.height};}}
      return null;
    }""")

def fill_button(page):
    return js(page,"""() => {
      const bs=[...document.querySelectorAll('button')].filter(b=>(b.textContent||'').trim()==='Fill');
      for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>0&&r.x>=1000&&r.y>500&&r.y<800){return {x:r.x,y:r.y,w:r.width,h:r.height};}}
      return null;
    }""")

def visible_panel_texts(page):
    return js(page,"""() => {
      const out=[];
      document.querySelectorAll('button,p,span,label').forEach(el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el); if(r.width>0&&r.height>0&&r.x>=1000&&r.x<=1560&&r.y>=430&&r.y<=820&&s.display!=='none'&&s.visibility!=='hidden'){let t=(el.textContent||'').trim().replace(/\\s+/g,' '); if(t&&t.length<80)out.push({tag:el.tagName,text:t});}});
      const seen=new Set();const res=[]; for(const o of out){const k=o.tag+'|'+o.text;if(!seen.has(k)){seen.add(k);res.push(o);}} return res;
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
    # switch to Basic tab
    page.locator("button", has_text="Basic").first.click(); page.wait_for_timeout(1000)
    snap(page,"111_basic_tab")

    before=alignment_buttons(page)
    if before:
        # click first alignment button (left)
        b=before[0]; page.mouse.click(b["x"]+b["w"]/2,b["y"]+b["h"]/2); page.wait_for_timeout(800)
        after=alignment_buttons(page); snap(page,"112_alignment_1")
        rec("click_alignment_1", before=before, after=after)
        before=alignment_buttons(page)
        b=before[2]; page.mouse.click(b["x"]+b["w"]/2,b["y"]+b["h"]/2); page.wait_for_timeout(800)
        after=alignment_buttons(page); snap(page,"113_alignment_3")
        rec("click_alignment_3", before=before, after=after)

    before_visible=visible_panel_texts(page)
    fb=click_font_button(page)
    if fb: page.mouse.click(fb["x"]+fb["w"]/2, fb["y"]+fb["h"]/2)
    page.wait_for_timeout(1200)
    after_visible=visible_panel_texts(page); snap(page,"114_font_clicked")
    rec("click_font", clicked=fb, before=before_visible, after=after_visible)

    before_visible=visible_panel_texts(page)
    fill=fill_button(page)
    if fill: page.mouse.click(fill["x"]+fill["w"]/2, fill["y"]+fill["h"]/2)
    page.wait_for_timeout(1200)
    after_visible=visible_panel_texts(page); snap(page,"115_fill_clicked")
    rec("click_fill", clicked=fill, before=before_visible, after=after_visible)

    browser.close()

(TASK/"basic_interactions.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE", TASK/"basic_interactions.json")
