# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1500)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc_info:
        card.click()
    fc=fc_info.value; fc.set_files(str(ROOT/"test_images"/"文字测例.jpg"))
    page.wait_for_timeout(15000)
    # list all buttons with Enhance text and info
    els=page.locator("button, [role='button'], div.cursor-pointer").filter(has_text="Enhance")
    print("count", els.count())
    for i in range(els.count()):
        e=els.nth(i)
        try:
            print(i, repr(e.evaluate("el => el.outerHTML.slice(0,500)")), "box", e.bounding_box())
        except Exception as ex:
            print(i, ex)
    b.close()
