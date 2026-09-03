# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test")
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
    fc.value.set_files(str(ROOT/"test_images"/"低分辨率.JPG"))
    page.wait_for_timeout(12000)
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)
    def panel_text():
        return page.evaluate("""() => {
          const out=[];
          document.querySelectorAll('div,span,p,button,input,textarea').forEach(el=>{
            const r=el.getBoundingClientRect();
            if(r.width>0 && r.height>0 && r.x>1090 && r.x<1560 && r.y>430 && r.y<800){
              const t=(el.textContent||'').trim().replace(/\\s+/g,' ');
              const tag=el.tagName;
              if(t && t.length<80) out.push({tag,text:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
            }
          });
          return out;
        }""")
    print('BASIC panel text')
    for d in panel_text(): print(json.dumps(d,ensure_ascii=False))
    # click Adjust tab
    def click_tab(txt):
        b=page.locator("button", has_text=txt).all()
        for x in b:
            try:
                r=x.bounding_box()
                if r and 430<r['y']<490:
                    x.click(); page.wait_for_timeout(2000); return True
            except: pass
        return False
    click_tab('Adjust')
    print('--- after click Adjust tab ---')
    for d in panel_text(): print(json.dumps(d,ensure_ascii=False))
    b.close()
