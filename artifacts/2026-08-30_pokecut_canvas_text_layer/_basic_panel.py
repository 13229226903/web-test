# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test"); TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"
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
    def panel_html():
        return page.evaluate("""() => { const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic'); for(const b of bs){let el=b; for(let i=0;i<7;i++){ if(!el.parentElement)break; el=el.parentElement; if(el.textContent&&el.textContent.includes('Space'))return el.outerHTML;} } return ''; }""")
    # click Basic tab
    def click_tab(txt):
        return page.evaluate("""(txt)=>{const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()===txt); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>100&&r.height>30&&r.y>400){b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}} return false;}""", txt)
    print('click Basic', click_tab('Basic'))
    page.wait_for_timeout(1500)
    page.screenshot(path=str(TASK/'shots'/'45_basic_tab.png'))
    (TASK/'panel_basic_initial.html').write_text(panel_html(), encoding='utf-8')
    print('basic html size', len(panel_html()))
    browser.close()
