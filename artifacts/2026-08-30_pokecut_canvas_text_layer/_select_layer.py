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
    page.mouse.dblclick(900,500); page.wait_for_timeout(1200)
    ta=page.locator("textarea.fixed.h-px.w-px").first
    ta.fill("line1\nline2"); page.wait_for_timeout(1000); page.keyboard.press("Escape"); page.wait_for_timeout(1000)
    page.locator("button[data-tool-id='layer']").first.click(); page.wait_for_timeout(1500)
    # click Text layer item button
    locs=page.locator("button", has_text="Text").all()
    for b in locs:
        r=b.bounding_box()
        if r and r['x']<500 and r['y']>250:
            page.mouse.click(r['x']+r['width']/2, r['y']+r['height']/2); break
    page.wait_for_timeout(1500)
    print('panel Basic count', page.locator("button", has_text="Basic").count())
    print('panel Space count', page.locator("button", has_text="Space").count())
    print('body', page.locator("body").inner_text()[:1500].replace('\n',' | '))
    browser.close()
