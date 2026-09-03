# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'; IMG=r'D:\Test\web-test\data\debug\test_photo.png'
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True); p=b.new_page(viewport={'width':1440,'height':1000}); p.goto(URL,wait_until='domcontentloaded'); p.wait_for_timeout(6000); p.set_input_files('#singleUploadInput',IMG); p.wait_for_timeout(8000)
 for name in ['Enhance Text','Remove Glare','Remove Moire','Document Scanner']:
  btn=p.locator('button', has_text=name).nth(0)
  print('\n###',name); print(btn.evaluate('el=>el.outerHTML'))
 b.close()
