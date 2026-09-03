# -*- coding: utf-8 -*-
"""Safe PC interaction exploration: toggles, scale and tooltip only; no Enhance generation."""
import json, pathlib
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test'); OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'; IMG=ROOT/'data/debug/test_photo.png'

def snapshot(page):
    return {
      'url': page.evaluate('location.href'),
      'effects': page.evaluate("""Array.prototype.map.call(document.querySelectorAll('[data-effect]'),function(el){return {effect:el.getAttribute('data-effect'),text:el.innerText.trim(),pressed:el.getAttribute('aria-pressed'),disabled:el.getAttribute('aria-disabled'),className:el.className};})"""),
      'scales': page.evaluate("""Array.prototype.map.call(document.querySelectorAll('p'),function(el){var t=el.innerText.trim();if(!['2k','4k','8k'].includes(t))return null;var item=el.closest('.cursor-pointer')||el.parentElement;var box=item.parentElement;return {scale:t,itemOuter:item.outerHTML,boxVisible:!!(box.offsetWidth||box.offsetHeight),boxHeight:box.getBoundingClientRect().height,boxText:box.innerText,boxClass:box.className};}).filter(Boolean)"""),
      'main': page.evaluate("""(function(){var el=document.querySelector('[data-enhance-action=desktop-primary]');if(!el)return null;var cost=el.querySelector('[data-text-enhance-total-cost]');return {outer:el.outerHTML,text:el.innerText,className:el.className,state:cost?cost.getAttribute('data-text-enhance-cost-state'):null,cost:cost?cost.innerText:null};})()"""),
      'panelText': page.evaluate("""(function(){var el=document.querySelector('[data-enhance-action=desktop-primary]');var root=el&&el.parentElement;return root?root.innerText.slice(0,1000):'';})()"""),
    }

with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True); page=browser.new_page(viewport={'width':1440,'height':1000})
  page.goto(URL,wait_until='domcontentloaded',timeout=45000); page.wait_for_timeout(6000)
  page.set_input_files('#singleUploadInput',str(IMG)); page.wait_for_timeout(10000)
  records=[]
  def record(label, shot=False):
    s=snapshot(page); records.append({'step':label,**s});
    print('\n### '+label); print(json.dumps(s,ensure_ascii=False,indent=2))
    if shot: page.screenshot(path=str(OUT/f'interaction_{label}.png'))
  record('01_after_upload_default',True)

  page.click('[data-effect="enhance_text"]'); page.wait_for_timeout(600)
  record('02_no_effect_selected',True)

  page.click('[data-effect="remove_glare"]'); page.wait_for_timeout(500)
  record('03_only_remove_glare')
  page.click('[data-effect="remove_moire"]'); page.wait_for_timeout(500)
  record('04_glare_moire')
  page.click('[data-effect="document_scanner"]'); page.wait_for_timeout(500)
  record('05_three_non_upscale_effects',True)

  page.click('[data-effect="enhance_text"]'); page.wait_for_timeout(500)
  record('06_all_four_effects_default_2k',True)
  page.get_by_text('4k',exact=True).click(); page.wait_for_timeout(500)
  record('07_all_four_effects_4k')
  page.get_by_text('8k',exact=True).click(); page.wait_for_timeout(500)
  record('08_all_four_effects_8k',True)

  for effect in ['enhance_text','remove_glare','remove_moire','document_scanner']:
    page.click(f'[data-effect="{effect}"]'); page.wait_for_timeout(300)
  record('09_no_effect_after_full_matrix',True)

  tooltips=[]
  for effect in ['enhance_text','remove_glare','remove_moire','document_scanner']:
    page.locator(f'[data-effect="{effect}"] [data-effect-help-icon]').hover(); page.wait_for_timeout(1200)
    text=page.evaluate('document.body.innerText'); tooltips.append({'effect':effect,'bodyText':text})
    print('\n### tooltip_'+effect); print(text[:1500])
    page.screenshot(path=str(OUT/f'interaction_tooltip_{effect}.png'),full_page=False)
  (OUT/'explore_desktop_interactions.json').write_text(json.dumps({'records':records,'tooltips':tooltips},ensure_ascii=False,indent=2),encoding='utf-8')
  browser.close()
