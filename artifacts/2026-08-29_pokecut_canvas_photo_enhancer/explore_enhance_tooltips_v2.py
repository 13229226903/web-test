# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-29_pokecut_canvas_photo_enhancer"
out={"tooltips":{}}
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
    for name in ["Standard Mode","Old Photo Mode","Portrait Mode","Text Mode","Ultra HD Mode"]:
        row=panel.locator("[data-enhance-row]").filter(has_text=name).first
        before=set(page.locator("body").inner_text().splitlines())
        row.locator("img[src*='enhance_help']").first.hover()
        page.wait_for_timeout(1200)
        after=set(page.locator("body").inner_text().splitlines())
        out["tooltips"][name]=[x for x in page.locator("body").inner_text().splitlines() if x not in before and x.strip()]
        # move mouse away
        page.mouse.move(10,10)
        page.wait_for_timeout(400)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    b.close()
(TASK/"explore_enhance_tooltips_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
