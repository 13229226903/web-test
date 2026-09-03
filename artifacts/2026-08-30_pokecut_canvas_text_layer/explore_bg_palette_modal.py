# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
from PIL import Image, ImageChops
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
OUT={"steps":[]}
def rec(name,**kw): OUT["steps"].append({"name":name,**kw}); print(json.dumps({"name":name,**kw},ensure_ascii=False)[:2500])
def snap(page,name): path=SHOTS/f"{name}.png"; page.screenshot(path=str(path)); return path
def js(page,expr,arg=None): return page.evaluate(expr,arg)
def diff_metric(p1,p2):
    im1=Image.open(p1).convert('RGB'); im2=Image.open(p2).convert('RGB')
    diff=ImageChops.difference(im1,im2); bbox=diff.getbbox()
    if not bbox: return {'bbox':None,'nonzero_pixels':0,'mean_abs':0.0}
    total=im1.size[0]*im1.size[1]
    pixels=sum(1 for p in diff.getdata() if p!=(0,0,0))
    mean=sum(sum(p) for p in diff.getdata())/(total*3*255)
    return {'bbox':bbox,'nonzero_pixels':pixels,'mean_abs':round(mean,6)}

def bg_buttons(page):
    return js(page,"""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('button')].slice(0,3).map((b,i)=>{const br=b.getBoundingClientRect(); return {i,x:br.x,y:br.y,w:br.width,h:br.height,cls:b.className};});}}} return null;}""")

def modal_state(page):
    return js(page,"""() => {
      const hex=document.querySelector('input.hexInput');
      const sliders=[...document.querySelectorAll('input.colorSlider')];
      const tabs=[...document.querySelectorAll('p')].filter(p=>['HSL','RGB'].includes(p.textContent.trim()));
      return {hex:hex?hex.value:null, rgb:sliders.slice(0,3).map(s=>s.value), hsl_tab_cls: tabs.length? tabs[0].className:null, rgb_tab_cls: tabs.length? tabs[1].className:null};
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
    # expand background and open palette
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(800)
    info=page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const rr=row.getBoundingClientRect(); return {x:rr.x,y:rr.y,w:rr.width,h:rr.height};}} return null;}""")
    page.mouse.click(info['x']+info['w']/2, info['y']+info['h']/2); page.wait_for_timeout(1000)
    btns=bg_buttons(page)
    p_before=snap(page,"140_bg_before_palette")
    # click palette index1
    b=btns[1]; page.mouse.click(b['x']+b['w']/2,b['y']+b['h']/2); page.wait_for_timeout(2000)
    initial=modal_state(page); p_open=snap(page,"141_bg_palette_open")
    rec("click_background_palette_open", initial=initial, diff_open=diff_metric(p_before,p_open))
    # click HSL tab
    page.evaluate("""() => { const ps=[...document.querySelectorAll('p')].filter(p=>p.textContent.trim()==='HSL'); if(ps[0]) ps[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); }""")
    page.wait_for_timeout(1000)
    hsl=modal_state(page); p_hsl=snap(page,"142_bg_palette_hsl")
    rec("click_hsl_tab", after=hsl, diff=diff_metric(p_open,p_hsl))
    # click RGB tab
    page.evaluate("""() => { const ps=[...document.querySelectorAll('p')].filter(p=>p.textContent.trim()==='RGB'); if(ps[0]) ps[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); }""")
    page.wait_for_timeout(1000)
    rgb=modal_state(page); p_rgb=snap(page,"143_bg_palette_rgb")
    rec("click_rgb_tab", after=rgb, diff=diff_metric(p_hsl,p_rgb))
    # set hex to red
    page.locator("input.hexInput").fill("#ff0000")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1500)
    red=modal_state(page); p_red=snap(page,"144_bg_palette_red")
    rec("set_hex_red", after=red, diff=diff_metric(p_rgb,p_red))
    # close modal with Escape
    page.keyboard.press("Escape"); page.wait_for_timeout(1200)
    closed=modal_state(page); p_closed=snap(page,"145_bg_palette_closed")
    rec("close_palette_escape", after=closed, diff=diff_metric(p_red,p_closed))
    browser.close()
(TASK/"background_palette_modal.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE")
