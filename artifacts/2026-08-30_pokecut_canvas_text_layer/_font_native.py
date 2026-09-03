# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import sys, io, json
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
    page.locator("button", has_text="Basic").first.click(); page.wait_for_timeout(1500)
    # click Font with native element.click()
    r=page.evaluate("""() => { const bs=[...document.querySelectorAll('button')].filter(b=>(b.textContent||'').trim()==='Font'); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>100&&r.x>=1080){ b.click(); return {x:r.x,y:r.y}; }} return null; }""")
    print('font native click', r)
    page.wait_for_timeout(3000)
    # dump any elements whose text changes in panel region or whole page
    body=page.locator("body").inner_text()
    print('body snippet after click:', body[:2000].replace('\n',' | '))
    browser.close()
