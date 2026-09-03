# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    print("URL", page.url, "TITLE", page.title())
    body=page.locator("body").inner_text()
    print("has Trending Tools", "Trending Tools" in body)
    print("has Start from a Photo", "Start from a Photo" in body)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    print("card count", card.count())
    if card.count():
        print("visible", card.is_visible(), card.inner_text()[:200])
        with page.expect_file_chooser(timeout=30000) as fc:
            card.click()
        fc.value.set_files(str(ROOT/"test_images"/"文字测例.jpg"))
        page.wait_for_timeout(15000)
        print("after upload URL", page.url)
        print("body sample", page.locator("body").inner_text()[:1500].replace("\n"," | "))
    b.close()
