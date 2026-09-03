# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
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
    def sec():
        return page.evaluate("""() => {const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const content=row.nextElementSibling; const btns=[...row.querySelectorAll('button')]; const small=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;}); const toggle=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>0&&br.height>0&&br.width>=30&&br.width<=50&&br.height<=24;}); return {row_x:r.x,row_y:r.y,content:content?getComputedStyle(content).display:null, small:small.length,toggle:toggle.length?{x:toggle[0].getBoundingClientRect().x,y:toggle[0].getBoundingClientRect().y,cls:toggle[0].className}:null};}} return null;}""")
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(800)
    print('before', json.dumps(sec(),ensure_ascii=False))
    # expand via small mouse
    info=page.evaluate("""() => {const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const btns=[...row.querySelectorAll('button')]; const small=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width<=16&&br.height<=16;}); if(small[0]){const br=small[0].getBoundingClientRect(); return {x:br.x+br.width/2,y:br.y+br.height/2};}}} return null;}""")
    page.mouse.click(info['x'], info['y']); page.wait_for_timeout(1000)
    print('after small', json.dumps(sec(),ensure_ascii=False))
    info2=page.evaluate("""() => {const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const btns=[...row.querySelectorAll('button')]; const toggle=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width>=30&&br.width<=50&&br.height<=24;}); if(toggle[0]){const br=toggle[0].getBoundingClientRect(); return {x:br.x+br.width/2,y:br.y+br.height/2};}}} return null;}""")
    print('toggle pos', info2)
    page.mouse.click(info2['x'], info2['y']); page.wait_for_timeout(1000)
    print('after toggle', json.dumps(sec(),ensure_ascii=False))
    print('body snippet', page.locator('body').inner_text()[:1500].replace('\n',' | '))
    browser.close()
