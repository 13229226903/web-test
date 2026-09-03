# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-29_pokecut_canvas_photo_enhancer"; SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
out={"steps":[]}
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
    page.locator("button.toolbar-hover-button", has_text="Enhance").first.click()
    page.wait_for_timeout(4000)
    heading=page.get_by_text("AI Enhancer", exact=True).last
    panel=heading.locator("..")
    tips={}
    for name in ["Standard Mode","Old Photo Mode","Portrait Mode","Text Mode","Ultra HD Mode"]:
        row=panel.locator("[data-enhance-row]").filter(has_text=name).first
        help_icon=row.locator("img[src*='enhance_help']").first
        if help_icon.count():
            try:
                help_icon.scroll_into_view_if_needed()
                help_icon.hover()
                page.wait_for_timeout(1200)
                # capture visible tooltip-ish text
                txt=page.evaluate("""() => {
                  const els=Array.from(document.querySelectorAll('body *')).filter(e=>{const r=e.getBoundingClientRect(); const s=getComputedStyle(e); return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';});
                  return els.map(e=>e.textContent.trim()).filter(t=>t&&t.length<160);
                }""")
                tips[name]=txt[-10:]
                snap(page,f"04_tooltip_{name.replace(' ','_').lower()}")
            except Exception as e:
                tips[name]=f"hover_error:{e}"
        else:
            tips[name]="no_help_icon"
    out["steps"].append({"name":"04_tooltips","tips":tips})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    b.close()
(TASK/"explore_enhance_tooltips.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
