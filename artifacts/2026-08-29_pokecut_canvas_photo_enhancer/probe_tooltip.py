# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
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
    page.locator("button.toolbar-hover-button", has_text="Enhance").first.click()
    page.wait_for_timeout(4000)
    heading=page.get_by_text("AI Enhancer", exact=True).last; panel=heading.locator("..")
    row=panel.locator("[data-enhance-row]").filter(has_text="Standard Mode").first
    before=page.locator("body").inner_text()
    row.locator("img[src*='enhance_help']").first.hover()
    page.wait_for_timeout(1500)
    after=page.locator("body").inner_text()
    # print diff lines
    print("DIFF after hover (lines unique after):")
    bset=set(before.splitlines()); aset=set(after.splitlines())
    print("\n".join([x for x in after.splitlines() if x not in bset][:40]))
    b.close()
