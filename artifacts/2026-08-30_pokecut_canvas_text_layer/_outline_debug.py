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
    def sec(page,s):
        return page.evaluate("""(s)=>{const spans=[...document.querySelectorAll('span')].filter(x=>x.textContent.trim()===s); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1080){return {x:r.x,y:r.y,text:sp.textContent};}} return null;}""",s)
    print('outline before', sec(page,'Outline'))
    # click Background via locator
    page.locator("button", has_text="Background").first.click(); page.wait_for_timeout(1000)
    print('outline after bg click', sec(page,'Outline'))
    # scroll panel to bottom
    page.evaluate("""() => { const p=document.querySelector('.panel-scroll-y'); if(p){p.scrollTop=p.scrollHeight;} }""")
    page.wait_for_timeout(1000)
    print('outline after scroll', sec(page,'Outline'))
    print('scrollTop', page.evaluate("""() => { const p=document.querySelector('.panel-scroll-y'); return p?p.scrollTop:null;}"""))
    browser.close()
