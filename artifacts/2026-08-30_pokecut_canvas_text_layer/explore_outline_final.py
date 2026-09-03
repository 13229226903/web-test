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

section_info_js = """(section) => {
  const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section);
  for(const sp of spans){
    const r=sp.getBoundingClientRect();
    if(r.width>0 && r.x>=1080){
      const row=sp.parentElement;
      const content=row.nextElementSibling;
      const btns=[...row.querySelectorAll('button')];
      const small=btns.filter(b=>{const br=b.getBoundingClientRect(); return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;});
      const toggle=btns.filter(b=>{const br=b.getBoundingClientRect(); return br.width>0&&br.height>0&&br.width>=30&&br.width<=50&&br.height<=24;});
      const rr=row.getBoundingClientRect();
      return {row:{x:rr.x,y:rr.y,w:rr.width,h:rr.height}, row_tag:row.tagName,
        content_display: content?getComputedStyle(content).display:null,
        small: small.length?(()=>{const b=small[0].getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};})():null,
        toggle: toggle.length?(()=>{const b=toggle[0].getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,cls:toggle[0].className};})():null};
    }
  }
  return null;
}"""

def section_info(page, section):
    return js(page, section_info_js, section)

def click_small(page):
    return js(page, """(section) => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const btns=[...row.querySelectorAll('button')]; const small=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;}); if(small[0]){small[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}} return false; }""", "Outline")

def click_toggle(page):
    return js(page, """(section) => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const btns=[...row.querySelectorAll('button')]; const toggle=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width>=30&&br.width<=50&&br.height<=24;}); if(toggle[0]){toggle[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}} return false; }""", "Outline")

def content_buttons(page):
    return js(page, """(section) => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('button')].map(b=>({cls:b.className,bg:b.style.backgroundColor||null,alt:(b.querySelector('img')||{}).alt||null}));}}} return null; }""", "Outline")

def click_content_index(page, index):
    return js(page, """(opts) => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; if(bs[opts.index]){const b=bs[opts.index]; b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); const br=b.getBoundingClientRect(); return {x:Math.round(br.x),y:Math.round(br.y),index:opts.index};}}}} return null; }""", {"index":index})

def ranges(page):
    return js(page, """(section) => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('input[type=range]')].map(s=>({value:s.value,min:s.min,max:s.max,disabled:s.disabled}));}}} return null; }""", "Outline")

def set_ranges(page, values):
    return js(page, """(opts) => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const ss=[...content.querySelectorAll('input[type=range]')]; const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; ss.forEach((s,i)=>{if(i<opts.values.length){set.call(s,String(opts.values[i])); s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true}));}}); return ss.map(s=>s.value);}}} return null; }""", {"values":values})

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
    # Scroll outline into view
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(1000)

    before=section_info(page,"Outline")
    click_small(page); page.wait_for_timeout(1200)
    after=section_info(page,"Outline"); snap(page,"98_outline_expanded")
    rec("click_outline_dropdown", before=before, after=after)

    before=section_info(page,"Outline")
    click_toggle(page); page.wait_for_timeout(1200)
    after=section_info(page,"Outline"); snap(page,"99_outline_toggle_on")
    rec("click_outline_toggle", before=before, after=after)

    before_types=content_buttons(page)
    clicked=click_content_index(page,1); page.wait_for_timeout(1200)
    after_types=content_buttons(page); snap(page,"100_outline_type1")
    rec("click_outline_type1", before=before_types, after=after_types, clicked=clicked)

    clicked=click_content_index(page,13); page.wait_for_timeout(1200)
    after_colors=content_buttons(page); snap(page,"101_outline_color_red")
    rec("click_outline_color_red", clicked=clicked, after=after_colors)

    before_vals=ranges(page)
    after_vals=set_ranges(page,[70,20,10,30]); page.wait_for_timeout(1200)
    snap(page,"102_outline_sliders")
    rec("set_outline_sliders", before=before_vals, after=after_vals)

    browser.close()

(TASK/"outline_interactions.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE", TASK/"outline_interactions.json")
