# -*- coding: utf-8 -*-
"""PRD full page-map exploration for ai-image-text-enhancer.
Writes state/button evidence for the current task artifact only.
"""
import json, pathlib, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = pathlib.Path(r'D:\Test\web-test')
TASK = '2026-08-26_pokecut_text_enhancer_prd_full'
OUT = ROOT / 'artifacts' / TASK
OUT.mkdir(parents=True, exist_ok=True)
URL = 'http://10.17.1.66:3001/tools/ai-image-text-enhancer'
IMG = ROOT / 'test_images' / 'gzy_comfytextart_PokeCut_1750754427032_4i88AV_meta_dev_cross_result.jpg'
EMAIL = '450832596@qq.com'
CODE = '123456'
MODES = ['enhance_text','remove_glare','remove_moire','document_scanner']

def shot(page, name, full=False):
    path = OUT / f'{name}.png'
    try:
        page.screenshot(path=str(path), full_page=full)
    except Exception as e:
        return {'path': str(path), 'error': str(e)}
    return {'path': str(path)}

def visible_buttons(page):
    return page.evaluate("""() => {
      const vis = (el) => { const r=el.getBoundingClientRect(); const s=getComputedStyle(el); return r.width>0 && r.height>0 && s.display!=='none' && s.visibility!=='hidden'; };
      const nodes = Array.from(document.querySelectorAll('button,a,input,label,[role="button"],[data-effect],[data-enhance-action],[data-text-enhance-total-cost],select,textarea'));
      return nodes.filter(vis).map((el) => {
        const r=el.getBoundingClientRect(); const attrs={};
        ['id','name','type','placeholder','href','role','aria-label','aria-pressed','aria-disabled','disabled','data-effect','data-effect-help-icon','data-enhance-action','data-text-enhance-cost-state'].forEach(k => { const v=el.getAttribute(k); if(v!==null) attrs[k]=v; });
        return {tag:el.tagName.toLowerCase(), text:(el.innerText||el.textContent||'').trim().replace(/\s+/g,' ').slice(0,160), attrs, className:String(el.className||'').slice(0,300), rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}};
      });
    }""")

def effects(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed'),text:(el.innerText||'').trim(),className:String(el.className||'')}))""")

def primary(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-enhance-action]')).map(el=>{const r=el.getBoundingClientRect(); const cost=el.querySelector('[data-text-enhance-total-cost]'); return {action:el.getAttribute('data-enhance-action'),text:(el.innerText||'').trim(),className:String(el.className||''),cost_state:cost&&cost.getAttribute('data-text-enhance-cost-state'),cost_text:cost&&(cost.innerText||'').trim(),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}}})""")

def body_has(page, s):
    try:
        return s in page.locator('body').inner_text(timeout=3000)
    except Exception:
        return False

def choose_effects(page, desired):
    for eff in MODES:
        want = eff in desired
        for _ in range(4):
            cur = {x['effect']: x['pressed']=='true' for x in effects(page)}.get(eff, False)
            if cur == want:
                break
            page.locator(f'[data-effect="{eff}"]').click(timeout=10000)
            page.wait_for_timeout(700)

def choose_scale(page, scale):
    # constrained to the processing panel by visible text; current DOM lacks data-scale.
    try:
        page.locator(f'p:text-is("{scale}")').first.click(timeout=10000)
        page.wait_for_timeout(700)
    except Exception as e:
        return str(e)
    return None

def snapshot(page, name, extra=None):
    rec = {'name': name, 'url': page.url, 'effects': effects(page), 'primary': primary(page), 'visible': visible_buttons(page), 'body_snippet': page.locator('body').inner_text(timeout=5000)[:3000]}
    if extra: rec.update(extra)
    shot(page, name)
    return rec

def login_and_predeploy(page):
    # switch debug panel to predeploy if possible
    res={'debug_switch': None, 'login': None}
    try:
        page.click('.debug-float-btn', timeout=5000); page.wait_for_timeout(800)
        page.locator('.environment-options .action-btn', has_text='预部署').click(timeout=5000); page.wait_for_timeout(6000)
        res['debug_switch']='predeploy_clicked'
    except Exception as e:
        res['debug_switch']='unavailable_or_failed: '+str(e)[:200]
    try:
        page.locator('button:has-text("Log in")').first.click(timeout=10000); page.wait_for_timeout(1200)
        page.locator('input[type="email"]').fill(EMAIL)
        page.locator('input[placeholder="Verification Code"]').fill(CODE)
        page.evaluate("""() => { for (const b of document.querySelectorAll('button')) { if ((b.innerText||'').trim()==='Log in' && b.offsetWidth>200) { b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true; } } return false; }""")
        page.wait_for_timeout(8000)
        res['login']='submitted'
    except Exception as e:
        res['login']='failed: '+str(e)[:200]
    return res

def wait_result(page, timeout=150):
    start=time.time(); records=[]
    while time.time()-start < timeout:
        page.wait_for_timeout(5000)
        txt=page.locator('body').inner_text(timeout=5000)
        rec={'elapsed': round(time.time()-start,1), 'continue': 'Continue Enhancing' in txt, 'edit_more':'Edit More' in txt, 'download':'Download' in txt, 'progress': re.findall(r'\b\d{1,3}%\b', txt)[:3], 'snippet': txt[:800]}
        records.append(rec)
        if rec['continue'] and rec['edit_more'] and rec['download'] and not rec['progress']:
            return True, records
    return False, records

result = {'url': URL, 'prd': r'D:\Test\my_project\gzy-feishu-doc-fetch\tmp\20260723_142302\02_文字画质增强实验优化(安国).md', 'image': str(IMG), 'states': []}
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={'width':1440,'height':1000}, locale='en-US', accept_downloads=True)
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(7000)
    result['states'].append(snapshot(page,'01_desktop_anonymous_initial'))
    page.set_input_files('#singleUploadInput', str(IMG)); page.wait_for_timeout(12000)
    result['states'].append(snapshot(page,'02_desktop_after_upload_default'))
    choose_effects(page, [])
    result['states'].append(snapshot(page,'03_desktop_no_effect_selected'))
    choose_effects(page, ['remove_glare'])
    result['states'].append(snapshot(page,'04_desktop_remove_glare_only'))
    choose_effects(page, ['remove_moire'])
    result['states'].append(snapshot(page,'05_desktop_remove_moire_only'))
    choose_effects(page, ['document_scanner'])
    result['states'].append(snapshot(page,'06_desktop_document_scanner_only'))
    choose_effects(page, MODES); choose_scale(page, '8k')
    result['states'].append(snapshot(page,'07_desktop_all_effects_8k'))
    # tooltips
    tips=[]
    for eff in MODES:
        try:
            loc = page.locator(f'[data-effect="{eff}"] [data-effect-help-icon]').first
            loc.hover(timeout=5000); page.wait_for_timeout(600)
            tips.append({'effect':eff,'body_contains':page.locator('body').inner_text(timeout=3000)[-1000:]})
            shot(page, f'08_tooltip_{eff}')
        except Exception as e:
            tips.append({'effect':eff,'error':str(e)[:200]})
    result['tooltips']=tips
    # login+predeploy+one generation default enhance_text
    result['login_predeploy']=login_and_predeploy(page)
    # After environment/login page may still have uploaded state, reload and re-upload for clean generation
    page.goto(URL, wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(6000)
    page.set_input_files('#singleUploadInput', str(IMG)); page.wait_for_timeout(12000)
    result['states'].append(snapshot(page,'09_predeploy_logged_after_upload_default'))
    try:
        page.locator('[data-enhance-action="desktop-primary"]').first.click(timeout=10000)
        page.wait_for_timeout(1500)
        result['states'].append(snapshot(page,'10_generation_processing_1s'))
        ok, records = wait_result(page, 150)
        result['generation']={'attempted': True, 'result_detected': ok, 'records': records}
        result['states'].append(snapshot(page,'11_generation_result'))
        # result buttons: download event and edit more navigation probe only if visible
        try:
            with page.expect_download(timeout=12000) as dl:
                page.locator('text=Download').first.click(timeout=10000)
            d=dl.value
            result['download']={'triggered':True,'suggested_filename':d.suggested_filename,'url':d.url}
        except Exception as e:
            result['download']={'triggered':False,'error':str(e)[:250]}
        result['states'].append(snapshot(page,'12_after_download_click'))
    except Exception as e:
        result['generation']={'attempted': True, 'error': str(e)[:500]}
    browser.close()

# mobile fresh context
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    device = pw.devices.get('iPhone 13') or {'viewport': {'width':390, 'height':844}, 'is_mobile': True, 'has_touch': True}
    ctx = browser.new_context(**device, locale='en-US')
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=60000); page.wait_for_timeout(7000)
    result['mobile_initial'] = snapshot(page,'13_mobile_initial')
    try:
        page.set_input_files('#file-upload', str(IMG)); page.wait_for_timeout(12000)
        result['mobile_after_upload'] = snapshot(page,'14_mobile_after_upload')
    except Exception as e:
        result['mobile_upload_error']=str(e)[:300]
    browser.close()

(OUT/'explore_text_enhancer_prd_full.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'states': len(result['states']), 'generation': result.get('generation',{}), 'download': result.get('download'), 'mobile_upload_error': result.get('mobile_upload_error')}, ensure_ascii=False, indent=2)[:4000])
