from playwright.sync_api import sync_playwright
URL='http://10.10..'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'; IMG=r'D:\Test\web-test\data\debug\test_photo.png'
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True); p=b.new_page(viewport={'width':1440,'height':1000}); p.goto(URL,wait_until='domcontentloaded'); p.wait_for_timeout(6000); p.set_input_files('#singleUploadInput',IMG); p.wait_for_timeout(8000)
 print(p.evaluate("""(()=>{let out='';document.querySelectorAll('p').forEach(p=>{if(['2k','4k','8k'].includes(p.innerText.trim())){let el=p;out += '\\n### '+p.innerText+'\\n';for(let i=0;i<4&&el;i++){out += el.tagName+' '+el.getAttribute('data-scale')+' '+el.className+'\\n';el=el.parentElement;}}});return out})()"""))
 b.close()
