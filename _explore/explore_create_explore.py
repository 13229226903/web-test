from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(r'D:\Test\web-test')
TASK=ROOT/'artifacts'/'2026-08-27_pokecut_infinite_canvas_inspire_me'
SHOTS=TASK/'shots'
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    c=b.new_context(viewport={'width':1920,'height':1080}, locale='en-US')
    page=c.new_page()
    page.goto('http://10.17.1.66:3001/create', wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    page.evaluate("() => [...document.querySelectorAll('.purchase-gift-modal')].forEach(n=>n.remove())")
    page.screenshot(path=str(SHOTS/'04_create_explore_default_viewport.png'), full_page=False)
    data=page.evaluate("""() => {
      const vis=el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
      return [...document.querySelectorAll('button,[role=button],a,input,textarea,[contenteditable=true]')].filter(vis).map(el=>({tag:el.tagName.toLowerCase(),text:(el.innerText||el.value||el.getAttribute('aria-label')||el.getAttribute('placeholder')||'').trim().replace(/\\s+/g,' ').slice(0,200),cls:(el.className||'').toString().slice(0,200),rect:(()=>{const r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}})()}))
    }""")
    (SHOTS/'create_default_inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    for i,x in enumerate(data): print(i,json.dumps(x,ensure_ascii=False))
    b.close()
