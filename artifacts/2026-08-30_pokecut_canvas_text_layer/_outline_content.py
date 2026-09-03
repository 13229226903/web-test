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
    # expand outline via small
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const btns=[...row.querySelectorAll('button')]; const small=btns.filter(b=>{const br=b.getBoundingClientRect();return br.width<=16&&br.height<=16;}); if(small[0]){small[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}}}} """)
    page.wait_for_timeout(1500)
    data=page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){const row=sp.parentElement; const content=row.nextElementSibling; if(content){ const bs=[...content.querySelectorAll('button')]; return bs.map((b,i)=>({i,cls:b.className.slice(0,80),bg:b.style.backgroundColor||null,alt:(b.querySelector('img')||{}).alt||null, x:Math.round(b.getBoundingClientRect().x), y:Math.round(b.getBoundingClientRect().y)})); }}} return null; }""")
    print(json.dumps(data,ensure_ascii=False,indent=1)[:5000])
    browser.close()
