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
    # expand Background and click palette index1
    page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){sp.parentElement.scrollIntoView({block:'center'});}} }""")
    page.wait_for_timeout(800)
    info=page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const rr=row.getBoundingClientRect(); return {x:rr.x,y:rr.y,w:rr.width,h:rr.height};}} return null;}""")
    page.mouse.click(info['x']+info['w']/2, info['y']+info['h']/2); page.wait_for_timeout(1000)
    btns=page.evaluate("""() => { const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background'); for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return [...content.querySelectorAll('button')].slice(0,3).map((b,i)=>{const br=b.getBoundingClientRect(); return {i,x:br.x,y:br.y,w:br.width,h:br.height};});}}} return null;}""")
    b=btns[1]; page.mouse.click(b['x']+b['w']/2,b['y']+b['h']/2); page.wait_for_timeout(2000)
    data=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('input,button,span,p,div').forEach(el=>{
        const r=el.getBoundingClientRect(); const s=getComputedStyle(el);
        if(r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'){
          let t=(el.value!==undefined?el.value:(el.textContent||'')).trim().replace(/\\s+/g,' ');
          if(t&&t.length<80 && r.y>700) out.push({tag:el.tagName,cls:el.className,type:el.type||null,placeholder:el.placeholder||null,text:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
        }
      });
      const seen=new Set(); const res=[]; for(const o of out){const k=o.tag+'|'+o.text+'|'+o.x+'|'+o.y; if(!seen.has(k)){seen.add(k);res.push(o);}} return res.slice(0,80);
    }""")
    print(json.dumps(data,ensure_ascii=False,indent=1))
    browser.close()
