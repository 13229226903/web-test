# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib, json, time
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test')
OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
IMG=ROOT/'test_images'/'gzy_comfytextart_PokeCut_1750754427032_4i88AV_meta_dev_cross_result.jpg'
EMAIL='450832596@qq.com'; CODE='123456'
MODES=['enhance_text','remove_glare','remove_moire','document_scanner']
ALL_EFFECTS=['enhance_text','remove_glare','remove_moire','document_scanner']
results={}
def state(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed'),text:(el.innerText||'').trim()}))""")
def wait_result(page, timeout=120):
    start=time.time()
    while time.time()-start<timeout:
        page.wait_for_timeout(2000)
        body=page.locator('body').inner_text()
        if 'Continue Enhancing' in body and 'Edit More' in body and 'Download' in body:
            return True, round(time.time()-start,1)
    return False, round(time.time()-start,1)
def set_only_mode(page, target):
    # 逐项修正，只保留 target 选中；若 target 因已处理提示第一次未选中，则再点一次
    for eff in ALL_EFFECTS:
        desired = (eff==target)
        for attempt in range(3):
            cur = next((x['pressed']=='true' for x in state(page) if x['effect']==eff), False)
            if cur==desired:
                break
            page.locator(f'[data-effect="{eff}"]').click(timeout=10000)
            page.wait_for_timeout(700)
        else:
            raise RuntimeError(f'无法将 {eff} 设置为 {desired}')
    # 最终校验
    st=state(page)
    if not (next(x['pressed']=='true' for x in st if x['effect']==target)) or sum(x['pressed']=='true' for x in st)!=1:
        raise RuntimeError(f'模式选择异常: {st}')
    return st
with sync_playwright() as pw:
    for mode in MODES:
        print(f'===== {mode} =====',flush=True)
        browser=pw.chromium.launch(headless=True)
        ctx=browser.new_context(viewport={'width':1440,'height':1000})
        page=ctx.new_page()
        page.goto(URL, wait_until='domcontentloaded', timeout=45000)
        page.wait_for_timeout(6000)
        # 切预部署
        page.click('.debug-float-btn', timeout=10000); page.wait_for_timeout(800)
        page.locator('.environment-options .action-btn', has_text='预部署').click(timeout=10000); page.wait_for_timeout(7000)
        # 登录
        page.locator('button:has-text("Log in")').first.click(timeout=10000); page.wait_for_timeout(1500)
        page.locator('input[type="email"]').fill(EMAIL)
        page.locator('input[placeholder="Verification Code"]').fill(CODE)
        page.evaluate("""() => { for (const b of document.querySelectorAll('button')) { if ((b.innerText||'').trim()==='Log in' && b.offsetWidth>200) { b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return; } } }""")
        page.wait_for_timeout(10000)
        # 上传
        page.set_input_files('#singleUploadInput', str(IMG)); page.wait_for_timeout(12000)
        # 只选择目标模式
        before_state=set_only_mode(page,mode)
        before_body=page.locator('body').inner_text()
        page.screenshot(path=str(OUT/f'all_modes_{mode}_before.png'), full_page=False)
        print('before_state',before_state,flush=True)
        # 生成
        page.click('[data-enhance-action="desktop-primary"]', timeout=10000)
        page.wait_for_timeout(1000)
        page.screenshot(path=str(OUT/f'all_modes_{mode}_processing_1s.png'), full_page=False)
        ok,elapsed=wait_result(page, 120)
        after_state=state(page)
        after_body=page.locator('body').inner_text()
        page.screenshot(path=str(OUT/f'all_modes_{mode}_result.png'), full_page=False)
        print('result',ok,'elapsed',elapsed,'after_state',after_state,flush=True)
        rec={'mode':mode,'result_detected':ok,'elapsed_sec':elapsed,'before_state':before_state,'after_state':after_state,'before_body':before_body,'after_body':after_body}
        # 非文本增强模式：测试已处理模式提示与两次点击
        if mode!='enhance_text':
            page.locator(f'[data-effect="{mode}"]').click(timeout=10000); page.wait_for_timeout(1500)
            warn_body=page.locator('body').inner_text()
            warn_state=state(page)
            page.screenshot(path=str(OUT/f'all_modes_{mode}_processed_click_1.png'), full_page=False)
            page.locator(f'[data-effect="{mode}"]').click(timeout=10000); page.wait_for_timeout(1500)
            second_body=page.locator('body').inner_text()
            second_state=state(page)
            page.screenshot(path=str(OUT/f'all_modes_{mode}_processed_click_2.png'), full_page=False)
            rec.update({'processed_click_1_body':warn_body,'processed_click_1_state':warn_state,'processed_click_2_body':second_body,'processed_click_2_state':second_state,'processed_notice_seen':'Please note that this image has been processed these effect' in warn_body})
            print('processed click1',warn_state,'notice',rec['processed_notice_seen'],flush=True)
            print('processed click2',second_state,flush=True)
        results[mode]=rec
        browser.close()
(OUT/'all_modes_generation_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('DONE')
