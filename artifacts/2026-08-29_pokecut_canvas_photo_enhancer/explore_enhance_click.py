# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-29_pokecut_canvas_photo_enhancer"; SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
out={"steps":[]}
def rec(page,name,extra=None):
    out["steps"].append({"name":name,"url":page.url,"extra":extra or {}}); print(name, extra or {})
def snap(page,name):
    p=SHOTS/f"{name}.png"; page.screenshot(path=str(p)); return str(p)
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
    snap(page,"10_canvas_before")
    top=page.locator("button.toolbar-hover-button", has_text="Enhance").first
    print("top count", top.count(), top.is_visible(), top.bounding_box())
    top.click()
    page.wait_for_timeout(5000)
    snap(page,"11_after_enhance_click")
    body=page.locator("body").inner_text()
    rec(page,"11_after_enhance_click",{"body_tail":body[-2500:]})
    print("BODY TAIL", body[-3000:])
    b.close()
(TASK/"explore_enhance_click.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
