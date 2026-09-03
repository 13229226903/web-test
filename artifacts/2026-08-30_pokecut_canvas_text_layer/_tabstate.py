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
    def active_tab():
        return page.evaluate("""() => { const out={}; for(const t of ['Basic','Adjust']) { const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()===t); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>100&&r.height>30&&r.y>400){ out[t]={cls:b.className, gradient:b.className.includes('gradient')}; }}} return out; }""")
    def panel_visible():
        return page.evaluate("""() => { const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic'); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>100&&r.height>30&&r.y>400)return true;} return false;}""")
    def findb(txt):
        return page.evaluate("""(txt)=>{const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()===txt); for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>0&&r.height>0&&r.y<450&&r.y>400)return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};} return null;}""", txt)
    print('after add', panel_visible(), active_tab())
    d=findb('Move Up'); page.mouse.click(d['x'],d['y']); page.wait_for_timeout(1200)
    print('after move up', panel_visible())
    d=findb('Adjust'); page.mouse.click(d['x'],d['y']); page.wait_for_timeout(1200)
    print('after adjust reopen', panel_visible(), active_tab())
    browser.close()
