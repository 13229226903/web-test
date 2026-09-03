# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib, json
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test')
OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
IMG=ROOT/'test_images'/'gzy_comfytextart_PokeCut_1750754427032_4i88AV_meta_dev_cross_result.jpg'
EMAIL='450832596@qq.com'; CODE='123456'
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True)
    ctx=b.new_context(viewport={'width':1440,'height':1000}); p=ctx.new_page()
    p.goto(URL, wait_until='domcontentloaded', timeout=45000); p.wait_for_timeout(6000)
    p.click('.debug-float-btn', timeout=10000); p.wait_for_timeout(800)
    p.locator('.environment-options .action-btn', has_text='预部署').click(timeout=10000); p.wait_for_timeout(7000)
    p.locator('button:has-text("Log in")').first.click(timeout=10000); p.wait_for_timeout(1500)
    p.locator('input[type="email"]').fill(EMAIL); p.locator('input[placeholder="Verification Code"]').fill(CODE)
    p.evaluate("""() => { for (const b of document.querySelectorAll('button')) { if ((b.innerText||'').trim()==='Log in' && b.offsetWidth>200) { b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return; } } }""")
    p.wait_for_timeout(10000)
    p.set_input_files('#singleUploadInput', str(IMG)); p.wait_for_timeout(12000)
    p.click('[data-enhance-action="desktop-primary"]', timeout=10000)
    # wait result
    for _ in range(30):
        p.wait_for_timeout(2000)
        body=p.locator('body').inner_text()
        if 'Continue Enhancing' in body and 'Edit More' in body and 'Download' in body:
            break
    states=p.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed'),text:el.innerText}))""")
    print('RESULT STATES',states)
    p.screenshot(path=str(OUT/'result_state_before_continue.png'), full_page=False)
    # click already processed mode to see warning
    p.locator('[data-effect="enhance_text"]').click(timeout=10000)
    p.wait_for_timeout(1500)
    body_after_click=p.locator('body').inner_text()
    print('AFTER PROCESSED CLICK BODY\n',body_after_click[:3000])
    p.screenshot(path=str(OUT/'result_processed_mode_click.png'), full_page=False)
    # click Continue Enhancing
    p.locator('text=Continue Enhancing').click(timeout=10000)
    p.wait_for_timeout(3000)
    states2=p.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed'),text:el.innerText}))""")
    print('AFTER CONTINUE STATES',states2)
    print('AFTER CONTINUE URL',p.url)
    print('AFTER CONTINUE BODY\n',p.locator('body').inner_text()[:3000])
    p.screenshot(path=str(OUT/'result_after_continue_enhancing.png'), full_page=False)
    b.close()
