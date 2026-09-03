# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib, json
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test')
OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
IMG=ROOT/'test_images'/'gzy_comfytextart_PokeCut_1750754427032_4i88AV_meta_dev_cross_result.jpg'
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
    p.locator('button:has-text("Log in")').first.click(timeout=10000)
    p.wait_for_timeout(1500)
    p.locator('input[type="email"]').fill(EMAIL)
    p.locator('input[placeholder="Verification Code"]').fill(CODE)
    p.evaluate("""() => {
      for (const b of document.querySelectorAll('button')) {
        if ((b.innerText||'').trim()==='Log in' && b.offsetWidth>200) {
          b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
          return;
        }
      }
    }""")
    p.wait_for_timeout(10000)
    # 上传
    p.set_input_files('#singleUploadInput', str(IMG))
    p.wait_for_timeout(12000)
    p.screenshot(path=str(OUT/'result_enhance_text_before_click.png'), full_page=False)
    print('BEFORE BODY\n',p.locator('body').inner_text()[:3000])
    # 确认默认模式
    effects=p.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed')}))""")
    print('EFFECTS',effects)
    p.click('[data-enhance-action="desktop-primary"]', timeout=10000)
    p.wait_for_timeout(1000)
    p.screenshot(path=str(OUT/'result_enhance_text_after_click.png'), full_page=False)
    result_detected=False
    records=[]
    for sec in [5,10,20,30,45,60,90,120]:
        p.wait_for_timeout(5000 if sec==5 else 5000)
        body=p.locator('body').inner_text()
        rec={'sec':sec,'url':p.url,'continue':'Continue Enhancing' in body,'edit_more':'Edit More' in body,'download':'Download' in body,'snippet':body[:1000]}
        records.append(rec)
        p.screenshot(path=str(OUT/f'result_enhance_text_{sec}s.png'), full_page=False)
        print('SNAP',sec,rec['continue'],rec['edit_more'],rec['download'],p.url)
        if rec['continue'] and rec['edit_more'] and rec['download']:
            result_detected=True
            break
    final_body=p.locator('body').inner_text()
    final_url=p.url
    print('FINAL URL',final_url)
    print('FINAL BODY\n',final_body[:5000])
    p.screenshot(path=str(OUT/'result_enhance_text_final.png'), full_page=False)
    result={'result_detected':result_detected,'final_url':final_url,'final_body':final_body,'records':records,'effects':effects}
    (OUT/'result_enhance_text.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    b.close()
