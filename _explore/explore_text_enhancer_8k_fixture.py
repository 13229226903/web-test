# -*- coding: utf-8 -*-
import json, pathlib, sys, time, re
from datetime import datetime
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(r'D:\Test\web-test')
TASK='2026-08-26_pokecut_text_enhancer_prd_full'
OUT=ROOT/'artifacts'/TASK
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
IMG=ROOT/'test_images'/'8K.jpg'

def shot(page,name):
    path=OUT/f'{name}.png'; page.screenshot(path=str(path),timeout=30000); return str(path.relative_to(ROOT)).replace('\\','/')
def effects(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-effect]')).map(el=>({effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed'),text:(el.innerText||'').trim().replace(/\s+/g,' '),className:String(el.className||'').slice(0,300)}))""")
def primary(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('[data-enhance-action]')).map(el=>{const cost=el.querySelector('[data-text-enhance-total-cost]'); const r=el.getBoundingClientRect(); return {text:(el.innerText||'').trim().replace(/\s+/g,' '), cost_state:cost&&cost.getAttribute('data-text-enhance-cost-state'), cost_text:cost&&(cost.innerText||'').trim(), className:String(el.className||'').slice(0,300), rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}}})""")
def scales(page):
    return page.evaluate("""() => {const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}; let out=[]; for(const el of document.querySelectorAll('p,span,button,div,label')){const t=(el.innerText||el.textContent||'').trim().toLowerCase(); if(!['2k','4k','8k'].includes(t)||!vis(el)) continue; const r=el.getBoundingClientRect(); let a=el, chain=[]; for(let i=0;i<4&&a;i++,a=a.parentElement) chain.push({tag:a.tagName.toLowerCase(),text:(a.innerText||a.textContent||'').trim().replace(/\s+/g,' ').slice(0,120),className:String(a.className||'').slice(0,250),ariaDisabled:a.getAttribute('aria-disabled'),disabled:a.getAttribute('disabled')}); out.push({text:t,className:String(el.className||'').slice(0,250),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},ancestors:chain});} return out;}""")
def modal(page):
    return page.evaluate("""() => {const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>80&&r.height>100&&s.display!=='none'&&s.visibility!=='hidden'}; return Array.from(document.querySelectorAll('div[class*=fixed],div[class*=modal],div[class*=dialog],[role=dialog]')).filter(vis).slice(0,10).map(el=>{const r=el.getBoundingClientRect(); return {text:(el.innerText||el.textContent||'').trim().replace(/\s+/g,' ').slice(0,800),className:String(el.className||'').slice(0,250),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}}})}""")
def snap(page,name,extra=None):
    body=page.locator('body').inner_text(timeout=6000)
    d={'name':name,'screenshot':shot(page,name),'url':page.url,'effects':effects(page),'primary':primary(page),'scales':scales(page),'modals':modal(page),'flags':{'highest_clarity':'The image is already at the highest clarity.' in body,'over_2k':'The resolution of the image is over 2K. Only larger options can be selected.' in body,'over_4k':'The resolution of the image is over 4K. Only larger options can be selected.' in body,'has_upscale':'Upscale to :' in body},'body_snippet':body[:3000]}
    if extra: d.update(extra)
    return d

def choose_modes(page, desired):
    out=[]
    for eff in ['enhance_text','remove_glare','remove_moire','document_scanner']:
        want=eff in desired
        for _ in range(4):
            cur={x['effect']:x['pressed']=='true' for x in effects(page)}.get(eff,False)
            if cur==want: break
            page.locator(f'[data-effect="{eff}"]').first.click(timeout=6000); page.wait_for_timeout(700)
        out.append({eff:{x['effect']:x['pressed']=='true' for x in effects(page)}.get(eff)})
    return out

res={'run_at':datetime.now().isoformat(),'image':str(IMG),'image_exists':IMG.exists(),'image_size_bytes':IMG.stat().st_size if IMG.exists() else None}
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True); ctx=browser.new_context(viewport={'width':1440,'height':1000},locale='en-US'); page=ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=70000); page.wait_for_timeout(7000)
    page.set_input_files('#singleUploadInput', str(IMG), timeout=20000); page.wait_for_timeout(15000)
    res['default']=snap(page,'60_8k_fixture_default')
    res['remove_glare_only_select']=choose_modes(page,['remove_glare'])
    page.wait_for_timeout(1000)
    res['remove_glare_only']=snap(page,'61_8k_fixture_remove_glare_only')
    browser.close()
(OUT/'explore_text_enhancer_8k_fixture.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'json':str(OUT/'explore_text_enhancer_8k_fixture.json'),'default_flags':res['default']['flags'],'default_primary':res['default']['primary'],'glare_flags':res['remove_glare_only']['flags'],'glare_primary':res['remove_glare_only']['primary'],'glare_effects':res['remove_glare_only']['effects']},ensure_ascii=False,indent=2))
