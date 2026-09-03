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
    def scroll_panel(top):
        page.evaluate("""(top)=>{const p=document.querySelector('.panel-scroll-y'); if(p)p.scrollTop=top;}""", top)
    def click_button_text(txt):
        return page.evaluate("""(txt)=>{const bs=[...document.querySelectorAll('button')].filter(b=>{const t=(b.textContent||'').trim().replace(/\\s+/g,' '); return t===txt;}); for(const b of bs){const r=b.getBoundingClientRect(); const s=getComputedStyle(b); if(r.width>100&&r.x>=1080&&s.display!=='none'){b.scrollIntoView({block:'center'}); b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};} } return null;}""", txt)
    def click_dropdown(section):
        return page.evaluate("""(section)=>{const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.x>=1080){let h=sp.parentElement; for(let i=0;i<4;i++){if(!h)break; h=h.parentElement;} if(h){const bs=[...h.querySelectorAll('button')]; const small=bs.filter(b=>{const br=b.getBoundingClientRect(); return br.width<=16&&br.height<=16;}); if(small.length){small[0].scrollIntoView({block:'center'}); small[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return {x:Math.round(small[0].getBoundingClientRect().x),y:Math.round(small[0].getBoundingClientRect().y)};}}} } return null;}""", section)
    def panel_html():
        return page.evaluate("""() => { const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic'); for(const b of bs){let el=b; for(let i=0;i<6;i++){ if(!el.parentElement)break; el=el.parentElement; if(el.textContent&&el.textContent.includes('Space'))return el.outerHTML;} } return ''; }""")
    # Background
    scroll_panel(0)
    r=click_button_text('Background'); print('bg click', r)
    page.wait_for_timeout(1500); page.screenshot(path=str(SHOTS/'57_background_expanded.png'))
    (TASK/'panel_background_expanded2.html').write_text(panel_html(),encoding='utf-8')
    # Outline
    scroll_panel(9999)
    r=click_dropdown('Outline'); print('outline dropdown', r)
    page.wait_for_timeout(1500); page.screenshot(path=str(SHOTS/'58_outline_expanded.png'))
    (TASK/'panel_outline_expanded2.html').write_text(panel_html(),encoding='utf-8')
    # Reflection similarly
    scroll_panel(0)
    r=click_dropdown('Reflection'); print('reflection dropdown', r)
    page.wait_for_timeout(1500); page.screenshot(path=str(SHOTS/'59_reflection_expanded.png'))
    (TASK/'panel_reflection_expanded2.html').write_text(panel_html(),encoding='utf-8')
    browser.close()
print('done')
