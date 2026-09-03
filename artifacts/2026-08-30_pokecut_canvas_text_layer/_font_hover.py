# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"; SHOTS=TASK/"shots"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc:
        card.click()
    fc.value.set_files(str(ROOT/"test_images"/"低分辨率.JPG"))
    page.wait_for_timeout(12000)
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)
    # Basic tab by locator
    page.locator("button", has_text="Basic").first.click(); page.wait_for_timeout(1500)
    font=page.locator("button", has_text="Font").first
    font.hover(); page.wait_for_timeout(1000)
    page.screenshot(path=str(SHOTS/'62_font_hover.png'))
    # query for elements with style font-family or text names
    res=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('*').forEach(el=>{
        const st=el.getAttribute&&el.getAttribute('style')||'';
        if(st.includes('font-family')||st.includes('fontFamily')){
          const r=el.getBoundingClientRect(); if(r.width>0&&r.height>0) out.push({tag:el.tagName,text:(el.textContent||'').trim().slice(0,40),style:st.slice(0,80),x:Math.round(r.x),y:Math.round(r.y)});
        }
      });
      return out.slice(0,40);
    }""")
    print('font-family styled elements after hover:', json.dumps(res,ensure_ascii=False,indent=1))
    browser.close()
