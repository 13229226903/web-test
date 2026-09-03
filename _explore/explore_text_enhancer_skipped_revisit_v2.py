# -*- coding: utf-8 -*-
import json, pathlib, re, sys, time, traceback
from datetime import datetime
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(r'D:\Test\web-test')
TASK='2026-08-26_pokecut_text_enhancer_prd_full'
OUT=ROOT/'artifacts'/TASK
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
CODE='123456'
ACCOUNTS={'member':'450832596@qq.com','single_purchase':'03201449879@qq.com','free':f'autotest{int(time.time())}@qq.com'}
IMAGES={'low_1k':ROOT/'test_images'/'1K.jpg','hi_4500_3000':ROOT/'test_images'/'4500_3000.png','hi_4k':ROOT/'test_images'/'4K.jpg','hi_4500_square':ROOT/'test_images'/'无人脸.jpg'}
MODES=['enhance_text','remove_glare','remove_moire','document_scanner']

def shot(page,name):
    path=OUT/f'{name}.png'; page.screenshot(path=str(path), timeout=30000); return str(path.relative_to(ROOT)).replace('\\','/')
def txt(page):
    try: return page.locator('body').inner_text(timeout=6000)
    except Exception as e: return f'<body error {e}>'
def primary(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-enhance-action]')).map(el=>{const cost=el.querySelector('[data-text-enhance-total-cost]'); const r=el.getBoundingClientRect(); return {text:(el.innerText||'').trim().replace(/\s+/g,' '), cost_state:cost&&cost.getAttribute('data-text-enhance-cost-state'), cost_text:cost&&(cost.innerText||'').trim(), className:String(el.className||''), rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}}})""")
def effects(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed'),text:(el.innerText||'').trim().replace(/\s+/g,' '),className:String(el.className||'')}))""")
def scales(page):
    return page.evaluate("""() => { const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}; let out=[]; for(const el of document.querySelectorAll('p,span,button,div,label')){const t=(el.innerText||el.textContent||'').trim().toLowerCase(); if(!['2k','4k','8k'].includes(t)||!vis(el)) continue; let a=el, chain=[]; for(let i=0;i<4&&a;i++,a=a.parentElement) chain.push({tag:a.tagName.toLowerCase(),text:(a.innerText||a.textContent||'').trim().replace(/\s+/g,' ').slice(0,120),className:String(a.className||'').slice(0,240),ariaDisabled:a.getAttribute('aria-disabled'),disabled:a.getAttribute('disabled')}); const r=el.getBoundingClientRect(); out.push({text:t,className:String(el.className||''),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},ancestors:chain}); } return out; }""")
def modal(page):
    return page.evaluate("""() => {const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>80&&r.height>100&&s.display!=='none'&&s.visibility!=='hidden'};return Array.from(document.querySelectorAll('div[class*=fixed],div[class*=modal],div[class*=dialog],[role=dialog]')).filter(vis).slice(0,10).map(el=>{const r=el.getBoundingClientRect(); return {text:(el.innerText||el.textContent||'').trim().replace(/\s+/g,' ').slice(0,1000),className:String(el.className||'').slice(0,240),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}}})}""")
def snap(page,name,extra=None):
    body=txt(page); d={'name':name,'url':page.url,'screenshot':shot(page,name),'primary':primary(page),'effects':effects(page),'scales':scales(page),'modals':modal(page),'flags':{'logged_in': bool(re.search(r'User[A-Z0-9]+|User8JY', body)) and 'Log in' not in body[:300], 'has_free': 'Free' in body, 'highest_clarity':'The image is already at the highest clarity.' in body, 'over_2k':'The resolution of the image is over 2K. Only larger options can be selected.' in body, 'over_4k':'The resolution of the image is over 4K. Only larger options can be selected.' in body}, 'body_snippet':body[:2500]}
    if extra: d.update(extra)
    return d
def goto(page): page.goto(URL, wait_until='domcontentloaded', timeout=70000); page.wait_for_timeout(7000)
def login(page,email):
    r={'email':email}
    try:
        if page.locator('input[type=email]').count()==0:
            try: page.locator('button:has-text("Log in")').first.click(timeout=10000)
            except Exception: page.get_by_text('Log in').first.click(timeout=10000)
            page.wait_for_timeout(1200)
        page.locator('input[type=email]').first.fill(email, timeout=10000)
        page.locator('input[placeholder="Verification Code"]').first.fill(CODE, timeout=10000)
        page.evaluate("""() => { for (const b of document.querySelectorAll('button')) { const t=(b.innerText||'').trim(), r=b.getBoundingClientRect(); if ((t==='Log in'||t==='Sign up') && r.width>100 && r.height>20) { b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return t; } } }""")
        page.wait_for_timeout(9000)
        if '/create' in page.url: goto(page)
        page.keyboard.press('Escape'); page.wait_for_timeout(300)
        body=txt(page); r.update({'ok': bool(re.search(r'User[A-Z0-9]+|User8JY', body)), 'url':page.url, 'has_login_button':'Log in' in body[:500]})
    except Exception as e: r.update({'ok':False,'error':str(e)[:500]})
    return r
def upload(page,k): page.set_input_files('#singleUploadInput', str(IMAGES[k]), timeout=15000); page.wait_for_timeout(13000)
def choose_scale(page,k):
    try: page.locator(f'p:text-is("{k}")').first.click(timeout=5000); page.wait_for_timeout(700); return {'scale':k,'clicked':True}
    except Exception as e: return {'scale':k,'clicked':False,'error':str(e)[:200]}
def choose_modes(page,desired):
    changes=[]
    for eff in MODES:
        want=eff in desired
        for _ in range(5):
            cur={x['effect']:x['pressed']=='true' for x in effects(page)}.get(eff,False)
            if cur==want: break
            page.locator(f'[data-effect="{eff}"]').first.click(timeout=6000); page.wait_for_timeout(600)
        changes.append({eff:{x['effect']:x['pressed']=='true' for x in effects(page)}.get(eff)})
    return changes
def switch_pre(page):
    r={}
    try:
        page.click('.debug-float-btn', timeout=6000); page.wait_for_timeout(800)
        page.locator('.environment-options .action-btn', has_text='预部署').click(timeout=6000); page.wait_for_timeout(7000)
        r['ok']=True
    except Exception as e: r={'ok':False,'error':str(e)[:400]}
    return r
def click_wait_short(page,seconds=20):
    r={'records':[]}
    try: page.locator('[data-enhance-action="desktop-primary"]').first.click(timeout=10000); r['clicked']=True
    except Exception as e: r['clicked']=False; r['click_error']=str(e)[:400]; return r
    end=time.time()+seconds
    while time.time()<end:
        page.wait_for_timeout(5000); body=txt(page); m=modal(page)
        item={'result': all(x in body for x in ['Continue Enhancing','Edit More','Download']),'progress':re.findall(r'\b\d{1,3}%\b',body)[:5],'modal':m[:2],'snippet':body[:800]}
        r['records'].append(item)
        if item['result'] or m: break
    if r['records']:
        last=r['records'][-1]
        r['outcome']='result' if last['result'] else ('modal' if last['modal'] else ('progress_or_waiting' if last['progress'] else 'no_result_observed'))
    return r

def network_bucket(page,b):
    def on_req(req):
        data=''
        try: data=req.post_data or ''
        except Exception: pass
        combo=(req.url+' '+data).lower()
        if any(k in combo for k in ['workflow','enhance','textenhance','comfyui','moire','reflection','scanner','realesrgan','credit','order','payment','subscribe','track','event']):
            b.append({'method':req.method,'url':req.url[:400],'post_data':data[:1000]})
    page.on('request',on_req)

def new(pw):
    br=pw.chromium.launch(headless=True); ctx=br.new_context(viewport={'width':1440,'height':1000},locale='en-US',accept_downloads=True); page=ctx.new_page(); return br,ctx,page

result={'run_at':datetime.now().isoformat(),'url':URL,'accounts':ACCOUNTS,'rule':'test-server first; predeploy fallback if generation fails; skip if both fail'}
with sync_playwright() as pw:
    # high-res UI
    print('highres...', flush=True); br,ctx,page=new(pw); hr=[]
    try:
        for i,k in enumerate(['hi_4500_3000','hi_4k','hi_4500_square'],1): goto(page); upload(page,k); hr.append(snap(page,f'50_highres_revisit_{i}_{k}',{'image_key':k}))
    finally: br.close()
    result['high_res_revisit']=hr
    (OUT/'explore_text_enhancer_skipped_revisit_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # account costs
    for label,email in [('member',ACCOUNTS['member']),('single_purchase',ACCOUNTS['single_purchase'])]:
        print(label,'...', flush=True); br,ctx,page=new(pw); snaps=[]; lr=None
        try:
            goto(page); lr=login(page,email); goto(page); upload(page,'low_1k'); snaps.append(snap(page,f'51_{label}_revisit_2k'))
            choose_scale(page,'4k'); snaps.append(snap(page,f'52_{label}_revisit_4k'))
            choose_scale(page,'8k'); snaps.append(snap(page,f'53_{label}_revisit_8k'))
            choose_modes(page,MODES); snaps.append(snap(page,f'54_{label}_revisit_all_8k'))
        finally: br.close()
        result[f'{label}_cost_revisit']={'login':lr,'snapshots':snaps}
        (OUT/'explore_text_enhancer_skipped_revisit_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # free purchase/quota probe on test + predeploy fallback observation
    for env in ['test','predeploy']:
        print('free',env,'...', flush=True); br,ctx,page=new(pw); net=[]; network_bucket(page,net); snaps=[]; lr=None; gen=None; sw=None
        try:
            goto(page); 
            if env=='predeploy': sw=switch_pre(page)
            lr=login(page,ACCOUNTS['free']); goto(page); upload(page,'low_1k'); snaps.append(snap(page,f'55_free_revisit_{env}_before'))
            gen=click_wait_short(page,25); snaps.append(snap(page,f'56_free_revisit_{env}_after'))
        finally: br.close()
        result[f'free_quota_{env}_revisit']={'switch':sw,'login':lr,'generation_probe':gen,'snapshots':snaps,'network':net[-40:]}
        (OUT/'explore_text_enhancer_skipped_revisit_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # multi-effect network evidence: click and observe 45s on member in test only; not considered server failure if only waiting.
    print('multi net...', flush=True); br,ctx,page=new(pw); net=[]; network_bucket(page,net); snaps=[]; lr=None; gen=None
    try:
        goto(page); lr=login(page,ACCOUNTS['member']); goto(page); upload(page,'low_1k'); choose_modes(page,MODES); choose_scale(page,'2k'); snaps.append(snap(page,'57_multi_effect_revisit_before'))
        gen=click_wait_short(page,45); snaps.append(snap(page,'58_multi_effect_revisit_after'))
    finally: br.close()
    result['multi_effect_order_revisit']={'login':lr,'generation_probe':gen,'snapshots':snaps,'network':net[-120:]}
    (OUT/'explore_text_enhancer_skipped_revisit_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'json':str(OUT/'explore_text_enhancer_skipped_revisit_v2.json'),'free_email':ACCOUNTS['free'],'keys':list(result.keys())},ensure_ascii=False,indent=2))
