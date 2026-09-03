from playwright.sync_api import sync_playwright
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'; IMG=r'D:\Test\web-test\data\debug\test_photo.png'
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True); p=b.new_page(viewport={'width':1440,'height':1000}); p.goto(URL,wait_until='domcontentloaded'); p.wait_for_timeout(6000); p.set_input_files('#singleUploadInput',IMG); p.wait_for_timeout(8000)
 # print ancestors for exact 2k,4k,8k and main parent
 for text in ['2k','4k','8k','Enhance']:
  print('\n###',text)
  items=p.evaluate("""(text)=>Array.prototype.filter.call(document.querySelectorAll('body p, body span'),function(el){return el.innerText.trim()===text}).map(function(el){return {outer:el.closest('button,[role=button],div.can-enhance-btn-bg,div.absolute')?.outerHTML||el.parentElement.outerHTML, html:el.outerHTML}})""",text)
  for x in items: print(x.get('outer','')[:5000])
 b.close()
