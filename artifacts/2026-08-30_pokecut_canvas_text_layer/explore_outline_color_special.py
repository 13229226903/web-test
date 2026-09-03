# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
from PIL import Image, ImageChops
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
OUT={"steps":[]}
def rec(name,**kw): OUT["steps"].append({"name":name,**kw}); print(json.dumps({"name":name,**kw},ensure_ascii=False)[:2200])
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

def outline_color_buttons(page):
    return js(page,"""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('button')].map((b,i)=>{const br=b.getBoundingClientRect(); return {i,cls:b.className,bg:b.style.backgroundColor||null,alt:(b.querySelector('img')||{}).alt||null,html:b.innerHTML.slice(0,120),x:br.x,y:br.y,w:br.width,h:br.height};}).slice(0,10);}}} return null;}""")

def modal_state(page):
    return js(page,"""() => { const hex=document.querySelector('input.hexInput'); return {hex:hex?hex.value:null, visible:!!(hex&&hex.getBoundingClientRect().width>0)}; }""")

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
    # expand outline dropdown
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const btns=[...row.querySelectorAll('button')]; const small=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;}); if(small[0]) small[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}} }""")
    page.wait_for_timeout(1200)
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(800)
    btns=outline_color_buttons(page)
    rec("outline_color_buttons", buttons=btns)
    # click color palette (index5)
    palette=btns[5]; p_before=snap(page,"160_outline_before_palette")
    page.mouse.click(palette['x']+palette['w']/2,palette['y']+palette['h']/2); page.wait_for_timeout(2000)
    m=modal_state(page); p_open=snap(page,"161_outline_palette_open")
    rec("click_outline_color_palette_open", clicked={"index":5,"alt":palette["alt"]}, modal=m, diff_open=diff_metric(p_before,p_open))
    page.keyboard.press("Escape"); page.wait_for_timeout(1000)
    m2=modal_state(page); p_closed=snap(page,"162_outline_palette_closed")
    rec("close_outline_palette_escape", modal_after=m2, diff=diff_metric(p_open,p_closed))
    # click picker (index6)
    btns=outline_color_buttons(page)
    picker=btns[6]; p_before2=snap(page,"163_outline_before_picker")
    page.mouse.click(picker['x']+picker['w']/2,picker['y']+picker['h']/2); page.wait_for_timeout(1500)
    p_mode=snap(page,"164_outline_picker_mode")
    rec("click_outline_color_picker_mode", clicked={"index":6,"html":picker["html"]}, diff_mode=diff_metric(p_before2,p_mode))
    page.mouse.click(900,500); page.wait_for_timeout(1500)
    p_applied=snap(page,"165_outline_picker_applied")
    after_btns=outline_color_buttons(page)
    rec("click_canvas_apply_outline_picker", after_buttons=after_btns, diff_applied=diff_metric(p_mode,p_applied))
    browser.close()
(TASK/"outline_color_special.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE")
