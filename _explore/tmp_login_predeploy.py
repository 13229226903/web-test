# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test')
OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
EMAIL='450832596@qq.com'
CODE='123456'
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True)
    ctx=b.new_context(viewport={'width':1440,'height':1000})
    p=ctx.new_page()
    p.goto(URL, wait_until='domcontentloaded', timeout=45000)
    p.wait_for_timeout(6000)
    # 切预部署
    p.click('.debug-float-btn', timeout=10000)
    p.wait_for_timeout(800)
    p.locator('.environment-options .action-btn', has_text='预部署').click(timeout=10000)
    p.wait_for_timeout(7000)
    # 登录
    btn=p.locator('button:has-text("Log in")').first
    print('login button visible',btn.is_visible())
    btn.click(timeout=10000)
    p.wait_for_timeout(2000)
    print('after click email count',p.locator('input[type="email"]').count())
    if p.locator('input[type="email"]').count()==0:
        # Vue dispatch fallback
        p.evaluate("""() => {
          for (const b of document.querySelectorAll('button')) {
            if ((b.innerText||'').trim()==='Log in') {
              b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
            }
          }
        }""")
        p.wait_for_timeout(2000)
    p.screenshot(path=str(OUT/'login_form_predeploy.png'), full_page=False)
    p.locator('input[type="email"]').fill(EMAIL)
    p.locator('input[placeholder="Verification Code"]').fill(CODE)
    p.screenshot(path=str(OUT/'login_filled_predeploy.png'), full_page=False)
    # submit login: wide Log in button
    p.evaluate("""() => {
      for (const b of document.querySelectorAll('button')) {
        if ((b.innerText||'').trim()==='Log in' && b.offsetWidth>200) {
          b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
          return;
        }
      }
    }""")
    p.wait_for_timeout(10000)
    print('post login url',p.url)
    print('post login body\n',p.locator('body').inner_text()[:3000])
    p.screenshot(path=str(OUT/'login_after_predeploy.png'), full_page=False)
    # 打开 debug 确认环境与权益
    if p.locator('.debug-float-btn').count():
        p.click('.debug-float-btn', timeout=10000)
        p.wait_for_timeout(1000)
        text=p.locator('.debug-panel').inner_text()
        print('DEBUG PANEL\n',text)
        p.screenshot(path=str(OUT/'login_debug_panel_predeploy.png'), full_page=False)
    b.close()
