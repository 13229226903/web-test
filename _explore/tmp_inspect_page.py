# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib
from playwright.sync_api import sync_playwright
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True)
    p=b.new_page(viewport={'width':1440,'height':1000})
    p.goto(URL, wait_until='domcontentloaded', timeout=45000)
    p.wait_for_timeout(6000)
    print('URL',p.url)
    print('TITLE',p.title())
    print('BODY\n',p.locator('body').inner_text()[:5000])
    print('DEBUG COUNT',p.locator('.debug-float-btn').count())
    print('LOGIN COUNT',p.locator('button:has-text("Log in")').count())
    print('EMAIL COUNT',p.locator('input[type="email"]').count())
    b.close()
