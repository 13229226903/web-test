# -*- coding: utf-8 -*-
"""测试服直连探索文字增强生成态与结果区交互；不切换预部署。"""
import sys, json, time, re, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r'D:\Test\web-test')
OUT = ROOT / 'artifacts' / '2026-08-26_pokecut_text_enhancer'
URL = 'http://10.17.1.66:3001/tools/ai-image-text-enhancer'
IMG = ROOT / 'test_images' / 'gzy_comfytextart_PokeCut_1750754427032_4i88AV_meta_dev_cross_result.jpg'
EMAIL = '450832596@qq.com'
CODE = '123456'
result = {'environment':'test_server_direct','url':URL,'image':str(IMG)}
network=[]

def state(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el => ({
      effect: el.getAttribute('data-effect'), pressed: el.getAttribute('aria-pressed'),
      class: el.className, text: (el.innerText || '').trim(),
      rect: (() => { const r=el.getBoundingClientRect(); return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}; })()
    }))""")

def dom_probe(page):
    return page.evaluate("""() => {
      const wanted = ['Continue Enhancing','Edit More','Download','Enhance'];
      const out = {actions:[],images:[],text_candidates:[]};
      for (const el of document.querySelectorAll('a,button,[role="button"],[data-enhance-action],div,span')) {
        const text=(el.innerText||'').trim().replace(/\\s+/g,' ');
        if (!text || text.length>120 || !wanted.some(w => text===w || text.startsWith(w))) continue;
        const cs=getComputedStyle(el); const r=el.getBoundingClientRect();
        out.text_candidates.push({tag:el.tagName,role:el.getAttribute('role'),text,
          class:String(el.className||''),cursor:cs.cursor,pointer:cs.pointerEvents,
          disabled:el.disabled===true||el.getAttribute('aria-disabled'),
          attrs:Array.from(el.attributes).filter(a=>/^data-|href$/.test(a.name)).map(a=>[a.name,a.value]),
          rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}});
      }
      for (const el of document.querySelectorAll('img')) {
        const r=el.getBoundingClientRect();
        if (r.width < 10 || r.height < 10) continue;
        out.images.push({src:el.currentSrc||el.src,alt:el.alt,class:String(el.className||''),
          rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}});
      }
      for (const el of document.querySelectorAll('[data-enhance-action]')) {
        const r=el.getBoundingClientRect();
        out.actions.push({action:el.getAttribute('data-enhance-action'),tag:el.tagName,text:(el.innerText||'').trim(),
          class:String(el.className||''),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}});
      }
      return out;
    }""")

def wait_result(page, timeout=150):
    start=time.time(); seen={}
    while time.time()-start < timeout:
        page.wait_for_timeout(1000)
        body=page.locator('body').inner_text()
        seen={'continue':'Continue Enhancing' in body,'edit_more':'Edit More' in body,'download':'Download' in body,'progress':bool(re.search(r'([0-9]{1,3})%',body))}
        if seen['continue'] and seen['edit_more'] and seen['download'] and not seen['progress']:
            return True, round(time.time()-start,1), seen
    return False, round(time.time()-start,1), seen

def shot(page,name):
    page.screenshot(path=str(OUT/name), full_page=False)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
    page=ctx.new_page()
    page.on('request', lambda req: network.append({'method':req.method,'url':req.url,'post_data':(req.post_data or '')[:1000]}) if any(k in req.url.lower() for k in ['enhance','generation','image','task']) and req.resource_type in ['xhr','fetch'] else None)
    page.on('response', lambda res: network.append({'status':res.status,'url':res.url}) if any(k in res.url.lower() for k in ['enhance','generation','task']) else None)
    page.goto(URL, wait_until='domcontentloaded', timeout=45000); page.wait_for_timeout(6000)
    result['initial_debug_text']=page.locator('body').inner_text()[:500]
    # 直接登录测试服，不打开 DEBUG 面板、不切换预部署
    page.locator('button:has-text("Log in")').first.click(timeout=10000); page.wait_for_timeout(1500)
    page.locator('input[type="email"]').fill(EMAIL)
    page.locator('input[placeholder="Verification Code"]').fill(CODE)
    page.evaluate("""() => { for (const b of document.querySelectorAll('button')) {
      if ((b.innerText||'').trim()==='Log in' && b.offsetWidth>200) { b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true; } } return false; }""")
    page.wait_for_timeout(8000)
    result['logged_in_body']=page.locator('body').inner_text()[:500]
    result['effects_before_upload']=state(page)
    page.set_input_files('#singleUploadInput', str(IMG)); page.wait_for_timeout(12000)
    result['effects_after_upload']=state(page)
    result['dom_after_upload']=dom_probe(page)
    shot(page,'testserver_direct_00_after_upload.png')

    # 初始仅 Enhance Text，生成一次
    page.click('[data-enhance-action="desktop-primary"]', timeout=10000)
    page.wait_for_timeout(1200); shot(page,'testserver_direct_01_processing.png')
    ok,elapsed,seen=wait_result(page,150)
    result['first_generation']={'result_detected':ok,'elapsed_sec':elapsed,'markers':seen,'effects':state(page),'dom':dom_probe(page),'body':page.locator('body').inner_text()[:6000]}
    shot(page,'testserver_direct_02_result.png')

    # 已处理效果点击：第一次应出现提示；记录状态是否被切换
    page.locator('[data-effect="enhance_text"]').click(timeout=10000); page.wait_for_timeout(1800)
    body1=page.locator('body').inner_text()
    result['processed_click_1']={'notice':'Please note that this image has been processed these effect' in body1,'effects':state(page),'body':body1[:5000]}
    shot(page,'testserver_direct_03_processed_click_1.png')

    # 还原/选择未处理模式 Remove Glare，准备连续增强
    for attempt in range(3):
        st={x['effect']:x['pressed']=='true' for x in state(page)}
        if st.get('enhance_text') is False and st.get('remove_glare') is True: break
        if st.get('enhance_text') is True: page.locator('[data-effect="enhance_text"]').click(); page.wait_for_timeout(800)
        if not ({x['effect']:x['pressed']=='true' for x in state(page)}).get('remove_glare'):
            page.locator('[data-effect="remove_glare"]').click(); page.wait_for_timeout(1000)
    result['before_continue_enhancing']={'effects':state(page),'dom':dom_probe(page)}
    shot(page,'testserver_direct_04_before_continue.png')

    # 点击结果区主操作 Continue Enhancing，观察链式生成
    page.locator('text=Continue Enhancing').first.click(timeout=10000); page.wait_for_timeout(1800)
    shot(page,'testserver_direct_05_continue_processing.png')
    ok2,elapsed2,seen2=wait_result(page,180)
    result['second_generation']={'result_detected':ok2,'elapsed_sec':elapsed2,'markers':seen2,'effects':state(page),'dom':dom_probe(page),'body':page.locator('body').inner_text()[:6000]}
    shot(page,'testserver_direct_06_continue_result.png')

    # 结果态点击 Download，只捕获下载事件/建议文件名，不保存到用户目录
    try:
        with page.expect_download(timeout=10000) as dl:
            page.locator('text=Download').first.click(timeout=10000)
        download=dl.value
        result['download']={'triggered':True,'suggested_filename':download.suggested_filename,'url':download.url}
    except Exception as e:
        result['download']={'triggered':False,'error':type(e).__name__+': '+str(e)}
    page.wait_for_timeout(1500)
    result['after_download']={'effects':state(page),'body':page.locator('body').inner_text()[:3000]}
    shot(page,'testserver_direct_07_after_download_click.png')

    # 最后观察 Edit More：是否进入编辑器及 URL/DOM
    try:
        with page.expect_navigation(wait_until='domcontentloaded', timeout=15000):
            page.locator('text=Edit More').first.click(timeout=10000)
        page.wait_for_timeout(8000)
    except Exception as e:
        result['edit_more_navigation_error']=type(e).__name__+': '+str(e)
        page.wait_for_timeout(3000)
    result['after_edit_more']={'url':page.url,'title':page.title(),'body':page.locator('body').inner_text()[:6000],'effects':state(page)}
    shot(page,'testserver_direct_08_after_edit_more.png')

    result['network']=network[-200:]
    browser.close()

(OUT/'testserver_generation_interactions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'first_generation':result.get('first_generation',{}).get('elapsed_sec'),'second_generation':result.get('second_generation',{}).get('elapsed_sec'),'processed_notice':result.get('processed_click_1',{}).get('notice'),'download':result.get('download'),'after_edit_more_url':result.get('after_edit_more',{}).get('url')},ensure_ascii=False,indent=2))
