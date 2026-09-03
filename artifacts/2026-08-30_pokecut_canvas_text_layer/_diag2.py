# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
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
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)
    data=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('button').forEach(b=>{
        const r=b.getBoundingClientRect();
        const t=(b.textContent||'').trim().replace(/\\s+/g,' ');
        if(r.width>0 && r.height>0 && t){
          out.push({text:t.slice(0,80), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
        }
      });
      return out;
    }""")
    for d in data:
        if d['y']<250 or d['x']>1100:
            print(json.dumps(d,ensure_ascii=False))
    print('--- spans in top/panel ---')
    spans=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('span, p, input, textarea, select').forEach(b=>{
        const r=b.getBoundingClientRect();
        const t=(b.textContent||b.getAttribute('placeholder')||'').trim().replace(/\\s+/g,' ');
        if(r.width>0 && r.height>0 && t && (r.y<250 || r.x>1100)){
          out.push({tag:b.tagName, text:t.slice(0,60), x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
        }
      });
      return out.slice(0,100);
    }""")
    for s in spans:
        print(json.dumps(s,ensure_ascii=False))
    b.close()
