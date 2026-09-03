# -*- coding: utf-8 -*-
"""Safe exploration after upload. No generation/download/login actions."""
import json, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"D:\Test\web-test")
OUT = ROOT / "artifacts" / "2026-08-26_pokecut_text_enhancer"
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
IMAGE = ROOT / "data" / "debug" / "test_photo.png"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(URL, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)
    page.set_input_files("#singleUploadInput", str(IMAGE))
    page.wait_for_timeout(12000)
    page.screenshot(path=str(OUT / "explore_desktop_after_upload.png"), full_page=False)
    data = {
      "url": page.evaluate("location.href"),
      "title": page.evaluate("document.title"),
      "bodyText": page.evaluate("document.body.innerText"),
      "headings": page.evaluate("""Array.prototype.map.call(document.querySelectorAll('h1,h2,h3,h4'), function(el) { var r=el.getBoundingClientRect(); return {tag:el.tagName.toLowerCase(),text:(el.innerText||el.textContent||'').trim(),rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)}}; }).filter(function(x){return x.rect.width>0&&x.rect.height>0;})"""),
      "interactive": page.evaluate("""Array.prototype.filter.call(document.querySelectorAll('button,a,input,textarea,select,label,[role=button],[role=checkbox],[role=radio]'),function(el){var r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';}).map(function(el){var r=el.getBoundingClientRect(),a={};['id','name','type','placeholder','aria-label','aria-checked','aria-disabled','aria-selected','disabled','href','data-testid'].forEach(function(k){var v=el.getAttribute(k);if(v!==null)a[k]=v;});return {tag:el.tagName.toLowerCase(),text:(el.innerText||el.textContent||'').trim().slice(0,500),attrs:a,rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)}};})"""),
      "images": page.evaluate("""Array.prototype.filter.call(document.querySelectorAll('img'),function(el){var r=el.getBoundingClientRect();return r.width>0&&r.height>0;}).map(function(el){var r=el.getBoundingClientRect();return {src:el.currentSrc||el.src,alt:el.alt,rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)}};})"""),
    }
    (OUT / "explore_desktop_after_upload.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUT / "explore_desktop_after_upload.txt").write_text(data["bodyText"],encoding="utf-8")
    print(data["bodyText"][:5000])
    print("\nINTERACTIVE")
    for x in data["interactive"]:
      text=x["text"].replace("\n"," / ")[:180]
      print(f"{x['tag']} | {text} | {x['attrs']} | {x['rect']}")
    browser.close()
