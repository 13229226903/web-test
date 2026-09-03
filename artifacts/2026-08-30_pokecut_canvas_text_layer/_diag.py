# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
def snap(page,name):
    path=SHOTS/f"{name}.png"; page.screenshot(path=str(path)); print("SHOT", path)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc:
        card.click()
    fc.value.set_files(str(ROOT/"test_images"/"文字测例.jpg"))
    page.wait_for_timeout(12000)
    snap(page,"10_canvas_loaded")
    print("URL", page.url)
    # find text tool
    info=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('button[data-tool-id]').forEach(b=>{
        const r=b.getBoundingClientRect();
        out.push({tool:b.getAttribute('data-tool-id'), text:(b.textContent||'').trim(), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
      });
      return out;
    }""")
    print("TOOLS", json.dumps(info,ensure_ascii=False))
    text=page.locator("button[data-tool-id='text']")
    print("text tool visible", text.count(), text.is_visible() if text.count() else None)
    text.first.click()
    page.wait_for_timeout(3000)
    snap(page,"11_after_add_text")
    # dump buttons with text in top area
    btns=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('button').forEach(b=>{
        const r=b.getBoundingClientRect();
        const t=(b.textContent||'').trim();
        if(r.width>0 && r.height>0 && t && r.y<200){
          out.push({text:t.slice(0,60), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
        }
      });
      return out.slice(0,50);
    }""")
    print("TOP BUTTONS", json.dumps(btns,ensure_ascii=False,indent=1))
    # body sample
    print("BODY", page.locator("body").inner_text()[:2000].replace("\n"," | "))
    b.close()
