# -*- coding: utf-8 -*-
import json, pathlib
from playwright.sync_api import sync_playwright
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
OUT=pathlib.Path(r'D:\Test\web-test\artifacts\2026-08-26_pokecut_text_enhancer')
IMG=pathlib.Path(r'D:\Test\web-test\data\debug\test_photo.png')
texts=['Choose the Effect','*Supports multiple selections','Enhance Text','Remove Glare','Remove Moire','Document Scanner','Upscale to :','2k','2048 * 2048 px','4k','4096 * 4096 px','8k','8192 * 8192 px','Enhance','2']
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True); p=b.new_page(viewport={'width':1440,'height':1000})
 p.goto(URL,wait_until='domcontentloaded'); p.wait_for_timeout(6000); p.set_input_files('#singleUploadInput',str(IMG)); p.wait_for_timeout(10000)
 p.screenshot(path=str(OUT/'explore_desktop_controls.png'))
 found=[]
 for text in texts:
  matches=p.evaluate("""(text) => Array.prototype.filter.call(document.querySelectorAll('body *'), function(el) {
    var own=Array.prototype.filter.call(el.childNodes,function(n){return n.nodeType===3}).map(function(n){return n.data.trim()}).join(' ');
    return own === text;
  }).map(function(el) {var r=el.getBoundingClientRect(),a={};for(var i=0;i<el.attributes.length;i++){a[el.attributes[i].name]=el.attributes[i].value;}return {text:text,tag:el.tagName.toLowerCase(),attrs:a,rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)},parentTag:el.parentElement&&el.parentElement.tagName.toLowerCase(),parentClass:el.parentElement&&el.parentElement.className,parentText:(el.parentElement&&(el.parentElement.innerText||'')).slice(0,300)};})""",text)
  found.extend(matches)
 (OUT/'explore_desktop_controls.json').write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding='utf-8')
 for x in found:
  print(json.dumps(x,ensure_ascii=False)[:1200])
 b.close()
