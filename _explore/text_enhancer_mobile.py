# -*- coding: utf-8 -*-
import json,pathlib
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test'); OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'; URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'; IMG=ROOT/'data/debug/test_photo.png'
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True); device=pw.devices['iPhone 13']; p=b.new_page(**device)
 p.goto(URL,wait_until='domcontentloaded',timeout=45000); p.wait_for_timeout(8000)
 p.set_input_files('input[type=file]',str(IMG)); p.wait_for_timeout(10000)
 p.screenshot(path=str(OUT/'explore_mobile_after_upload.png'),full_page=False)
 data={'viewport':{'width':p.viewport_size['width'],'height':p.viewport_size['height']},'bodyText':p.evaluate('document.body.innerText'),'fileInputs':p.evaluate("""Array.prototype.map.call(document.querySelectorAll('input[type=file]'),function(x){return {id:x.id,multiple:x.multiple};})"""),'effects':p.evaluate("""Array.prototype.map.call(document.querySelectorAll('[data-effect]'),function(el){var r=el.getBoundingClientRect();return {effect:el.getAttribute('data-effect'),text:el.innerText.trim(),pressed:el.getAttribute('aria-pressed'),disabled:el.getAttribute('aria-disabled'),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},className:String(el.className)};})"""),'scales':p.evaluate("""Array.prototype.map.call(document.querySelectorAll('p'),function(el){var t=el.innerText.trim();if(!['2k','4k','8k'].includes(t))return null;var item=el.closest('.cursor-pointer')||el.parentElement;var box=item.parentElement;var r=box.getBoundingClientRect();return {scale:t,boxText:box.innerText,rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},boxClass:String(box.className),itemOuter:item.outerHTML};}).filter(Boolean)"""),'primary':p.evaluate("""Array.prototype.map.call(document.querySelectorAll('[data-enhance-action]'),function(el){var r=el.getBoundingClientRect();return {action:el.getAttribute('data-enhance-action'),text:el.innerText,className:String(el.className),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},outer:el.outerHTML};})""")}
 (OUT/'explore_mobile_after_upload.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:data[k] for k in ['viewport','fileInputs','effects','scales','primary']},ensure_ascii=False,indent=2)); print('PANEL\n'+data['bodyText'][:1200])
 b.close()
