# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib, json
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test')
OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True)
    p=b.new_page(viewport={'width':1440,'height':1000})
    p.goto(URL, wait_until='domcontentloaded', timeout=45000)
    p.wait_for_timeout(6000)
    p.click('.debug-float-btn', timeout=10000)
    p.wait_for_timeout(1500)
    p.screenshot(path=str(OUT/'predeploy_panel_before_switch.png'), full_page=False)
    print('PANEL TEXT\n',p.locator('.debug-panel').inner_text())
    btn=p.locator('.environment-options .action-btn', has_text='预部署')
    print('PREDEPLOY COUNT',btn.count())
    if btn.count()!=1:
        raise RuntimeError('predeploy button not unique')
    btn.click(timeout=10000)
    p.wait_for_timeout(7000)
    print('AFTER URL',p.url)
    print('AFTER BODY\n',p.locator('body').inner_text()[:2000])
    p.screenshot(path=str(OUT/'predeploy_after_switch.png'), full_page=False)
    b.close()
