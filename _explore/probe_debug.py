import sys, json, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
root = pathlib.Path(r'D:\Test\web-test')
out = root/'artifacts'/'2026-08-26_pokecut_text_enhancer'
url='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.goto(url, wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(8000)
    candidates=page.locator('text=DEBUG')
    print('debug candidates', candidates.count())
    if candidates.count()>0:
        try:
            candidates.first.click(timeout=5000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print('debug click failed',repr(e))
    body=page.locator('body').inner_text()
    page.screenshot(path=str(out/'debug_panel_open.png'), full_page=False)
    print(json.dumps({'url':page.url,'title':page.title(),'body_snippet':body[:3000]},ensure_ascii=False,indent=2))
    browser.close()
