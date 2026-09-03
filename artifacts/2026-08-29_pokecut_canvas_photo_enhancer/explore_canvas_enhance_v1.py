# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, time
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-29_pokecut_canvas_photo_enhancer"; SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
out={"task_id":"2026-08-29_pokecut_canvas_photo_enhancer","steps":[]}
def rec(page,name,extra=None):
    out["steps"].append({"name":name,"url":page.url,"extra":extra or {}})
def snap(page,name):
    p=SHOTS/f"{name}.png"; page.screenshot(path=str(p), full_page=False); return str(p)
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
    rec(page,"01_canvas_loaded",{"title":page.title(),"toolbar_enhance_count":page.locator("button.toolbar-hover-button", has_text="Enhance").count(),"bottom_enhance_count":page.locator("button", has_text="Enhance").count()})
    snap(page,"01_canvas_loaded")
    top=page.locator("button.toolbar-hover-button", has_text="Enhance").first
    top.click()
    page.wait_for_timeout(4000)
    panel=page.locator("div.absolute.z-\\[70\\]").last if False else page.locator("div[data-no-capture='true']").filter(has_text="AI Enhancer").last
    # More robust panel by heading parent
    heading=page.get_by_text("AI Enhancer", exact=True).last
    panel=heading.locator("..")
    rec(page,"02_enhance_panel_open",{"panel_visible":panel.is_visible()})
    snap(page,"02_enhance_panel_open")
    # collect mode rows
    rows=panel.locator("[data-enhance-row]")
    modes=[]
    for i in range(rows.count()):
        row=rows.nth(i)
        txt=row.inner_text().replace("\n"," | ").strip()
        cls=row.get_attribute("class") or ""
        img_alts=[a.get_attribute("alt") for a in row.locator("img").all()]
        box=row.bounding_box()
        modes.append({"index":i,"text":txt,"class":cls,"img_alts":img_alts,"box":box,"selected":"ring-c-theme" in cls})
        # screenshot each mode default?
    rec(page,"03_modes",{"modes":modes})
    # click each mode text and record resolution line and selected
    mode_clicks={}
    for name in ["Standard Mode","Old Photo Mode","Portrait Mode","Text Mode","Ultra HD Mode"]:
        # use row by has_text and click button/label inside
        row=panel.locator("[data-enhance-row]").filter(has_text=name).first
        try:
            row.click()
        except Exception as e:
            # click the button inside if row itself fails
            btn=row.locator("button").first
            btn.click()
        page.wait_for_timeout(1500)
        body=panel.inner_text()
        selected=row.get_attribute("class") or ""
        # resolution text from row
        mode_clicks[name]={"row_text":row.inner_text().replace("\n"," | ").strip(),"selected":"ring-c-theme" in (row.get_attribute("class") or "")}
        snap(page,f"03_mode_{name.replace(' ','_').lower()}")
    rec(page,"04_mode_click_results",{"mode_clicks":mode_clicks})
    # current panel body
    body=panel.inner_text()
    rec(page,"05_panel_body",{"body":body})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    b.close()
(TASK/"explore_canvas_enhance_v1.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
