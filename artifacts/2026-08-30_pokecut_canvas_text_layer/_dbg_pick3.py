from playwright.sync_api import sync_playwright
from pathlib import Path
from PIL import Image
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test")
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
    # apply blue
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}} return false; }""")
    page.wait_for_timeout(1500)
    page.locator("input.hexInput").fill("#0000ff"); page.keyboard.press("Enter"); page.wait_for_timeout(1200); page.keyboard.press("Escape"); page.wait_for_timeout(1000)
    pal=Path('artifacts/2026-08-30_pokecut_canvas_text_layer/_dbg_pal3.png'); page.screenshot(path=str(pal))
    img=Image.open(pal).convert('RGB')
    best=None; bd=-1
    for y in range(307,853,2):
        for x in range(778,1142,2):
            r,g,b=img.getpixel((x,y))
            if max(r,g,b)>235 or max(r,g,b)<20: continue
            # avoid blue-ish: distance from blue
            d=((r-0)**2+(g-0)**2+(b-255)**2)**0.5
            if d>bd: bd=d; best=(x,y,(r,g,b))
    print('target', best, bd)
    # enter picker
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[2]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}} return false; }""")
    page.wait_for_timeout(1500)
    print('overlay before', page.locator('.color-picker-wrapper').count())
    page.mouse.move(best[0],best[1]); page.wait_for_timeout(300); page.mouse.click(best[0],best[1]); page.wait_for_timeout(1500)
    print('overlay after', page.locator('.color-picker-wrapper').count())
    browser.close()
