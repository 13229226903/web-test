# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
from PIL import Image, ImageChops
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
OUT={"steps":[]}
def rec(name,**kw): OUT["steps"].append({"name":name,**kw}); print(json.dumps({"name":name,**kw},ensure_ascii=False)[:2000])
def snap(page,name): path=SHOTS/f"{name}.png"; page.screenshot(path=str(path)); return path
def js(page,expr,arg=None): return page.evaluate(expr,arg)
def diff_metric(p1,p2):
    im1=Image.open(p1).convert('RGB'); im2=Image.open(p2).convert('RGB')
    diff=ImageChops.difference(im1,im2)
    bbox=diff.getbbox()
    if not bbox: return {'bbox':None,'nonzero_pixels':0,'mean_abs':0.0}
    pixels=sum(1 for p in diff.getdata() if p!=(0,0,0))
    total=im1.size[0]*im1.size[1]
    mean=sum(sum(p) for p in diff.getdata())/(total*3*255)
    return {'bbox':bbox,'nonzero_pixels':pixels,'mean_abs':round(mean,6)}

def reflection_info(page):
    return js(page,"""() => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; const btns=[...row.querySelectorAll('button')]; const small=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;}); const toggle=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width>=30&&br.width<=50&&br.height<=24;}); const rr=row.getBoundingClientRect(); return {row:{x:rr.x,y:rr.y,w:rr.width,h:rr.height}, content_display:content?getComputedStyle(content).display:null, small:small.length?(()=>{const b=small[0].getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height};})():null, toggle:toggle.length?(()=>{const b=toggle[0].getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,cls:toggle[0].className};})():null};}}
      return null;
    }""")
def reflection_values(page):
    return js(page,"""() => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('input.space-slider')].map(s=>({value:s.value,min:s.min,max:s.max,disabled:s.disabled}));}}}
      return null;
    }""")
def set_reflection_values(page,vals):
    return js(page,"""(vals) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');
      for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const ss=[...content.querySelectorAll('input.space-slider')]; const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; ss.forEach((s,i)=>{if(i<vals.length){set.call(s,String(vals[i])); s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true}));}}); return ss.map(s=>s.value);}}}
      return null;
    }""",vals)

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
    # open Reflection (scroll into view + small click)
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(800)
    info=reflection_info(page)
    small=info['small']; page.mouse.click(small['x']+small['w']/2,small['y']+small['h']/2); page.wait_for_timeout(1200)
    before=reflection_values(page)
    p_before=snap(page,"130_reflection_off")
    # toggle on
    info=reflection_info(page); toggle=info['toggle']; page.mouse.click(toggle['x']+toggle['w']/2,toggle['y']+toggle['h']/2); page.wait_for_timeout(1500)
    info_after=reflection_info(page); p_after=snap(page,"131_reflection_on")
    rec("reflection_toggle_on", before_toggle=info, after_toggle=info_after, values_before=before, diff=diff_metric(p_before,p_after))
    # adjust each param, screenshot after each
    prev=p_after
    for idx,name in enumerate(['scope','opacity','distance','angle']):
        vals=[100,50,0,180]
        vals[idx]=20 if idx<3 else 45
        after_vals=set_reflection_values(page,vals); page.wait_for_timeout(1200)
        p=snap(page,f"132_reflection_{name}")
        rec(f"set_reflection_{name}", before_values=reflection_values(page) if False else None, after_values=after_vals, diff=diff_metric(prev,p))
        prev=p
    # final values
    rec("reflection_final_values", values=reflection_values(page))
    browser.close()
(TASK/"reflection_effect.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE")
