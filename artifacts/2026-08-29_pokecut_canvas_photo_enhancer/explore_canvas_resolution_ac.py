# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-29_pokecut_canvas_photo_enhancer"
out={"images":[]}
def open_canvas(page, img):
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1500)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc_info:
        card.click()
    fc=fc_info.value; fc.set_files(str(ROOT/"test_images"/img))
    page.wait_for_timeout(15000)
    page.locator("button.toolbar-hover-button", has_text="Enhance").first.click()
    page.wait_for_timeout(4000)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    for img in ["1K.jpg","4K.jpg","4K.png","8K.jpg","低分辨率.JPG"]:
        open_canvas(page,img)
        heading=page.get_by_text("AI Enhancer", exact=True).last
        panel=heading.locator("..")
        rows=panel.locator("[data-enhance-row]")
        row_data=[]
        for i in range(rows.count()):
            row=rows.nth(i)
            row_data.append({"idx":i,"text":row.inner_text().replace("\n"," | ").strip(),"class":row.get_attribute("class")})
        body=panel.inner_text()
        html=page.content()
        entry={"img":img,"url":page.url,"row_data":row_data,"body":body,"strings":{s:(s in html) for s in ["2K","4K","8K","2048","4096","8192","Upscale","resolution"]}}
        out["images"].append(entry)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    b.close()
(TASK/"explore_canvas_resolution_ac.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
