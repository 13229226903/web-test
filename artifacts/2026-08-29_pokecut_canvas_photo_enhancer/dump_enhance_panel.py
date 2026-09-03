# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from pathlib import Path
ROOT=Path(r"D:\Test\web-test")
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
    # dump outerHTML of the AI Enhancer drawer/panel ancestors
    js = """() => {
      const find = (txt) => Array.from(document.querySelectorAll('*')).filter(e=>e.childNodes.length===1 && e.childNodes[0].nodeType===3 && e.textContent.trim()===txt).map(e=>e)[0];
      const el = find('AI Enhancer');
      if(!el) return 'not found';
      let chain=[]; let n=el;
      for(let i=0;i<6 && n;i++){ const r=n.getBoundingClientRect(); chain.push({tag:n.tagName, cls:String(n.className).slice(0,200), text:(n.innerText||'').slice(0,200), x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}); n=n.parentElement; }
      return JSON.stringify(chain,null,2);
    }"""
    print(page.evaluate(js))
    # outer html of parent
    print(page.evaluate("""() => {
      const el = Array.from(document.querySelectorAll('*')).find(e=>e.childNodes.length===1 && e.childNodes[0].nodeType===3 && e.textContent.trim()==='AI Enhancer');
      if(!el) return 'not found';
      const p=el.parentElement;
      return p ? p.outerHTML.slice(0,6000) : 'no parent';
    }"""))
    b.close()
