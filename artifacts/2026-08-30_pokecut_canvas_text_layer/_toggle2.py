# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test")
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
    def panel_visible():
        return page.evaluate("""() => {
          const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic');
          for(const b of bs){ const r=b.getBoundingClientRect(); if(r.width>100 && r.height>30 && r.y>400) return true; }
          return false;
        }""")
    print('initial', panel_visible())
    page.mouse.click(900, 300)
    page.wait_for_timeout(1500)
    print('after blank close', panel_visible())
    # click toolbar Adjust
    toolbar=page.locator("button", has_text="Adjust").all()
    clicked=False
    for bb in toolbar:
        try:
            r=bb.bounding_box()
            if r and 410<r['y']<440:
                page.mouse.click(r['x']+r['width']/2, r['y']+r['height']/2)
                clicked=True; print('clicked toolbar adjust', r)
                break
        except Exception as e: print('err',e)
    page.wait_for_timeout(1500)
    print('after toolbar adjust click, panel visible', panel_visible())
    browser.close()
