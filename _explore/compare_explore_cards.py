from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(r'D:\Test\web-test')
TASK=ROOT/'artifacts'/'2026-08-27_pokecut_infinite_canvas_inspire_me'
SHOTS=TASK/'shots'
def extract(page):
    return page.evaluate("""() => {
      const vis=el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
      const tabs=[...document.querySelectorAll('button')].filter(vis).map(b=>b.innerText.trim()).filter(t=>t && !['Sign up','Log in','DEBUG'].includes(t));
      const cards=[...document.querySelectorAll('div.absolute.cursor-pointer.group')].filter(vis).map(el=>{
        const r=el.getBoundingClientRect();
        const img=el.querySelector('img');
        const attrs={}; for(const a of el.attributes) attrs[a.name]=a.value;
        return {text:el.innerText.trim().replace(/\\s+/g,' '),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},attrs,img:img?{src:img.src,alt:img.alt,naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,cls:img.className}:null,html:el.outerHTML.slice(0,1000)}
      });
      return {url:location.href,tabs,cards}
    }""")
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    c=b.new_context(viewport={'width':1920,'height':1080}, locale='en-US')
    page=c.new_page()
    page.goto('http://10.17.1.66:3001/create', wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    page.evaluate("() => [...document.querySelectorAll('.purchase-gift-modal')].forEach(n=>n.remove())")
    create=extract(page)
    (SHOTS/'create_explore_cards.json').write_text(json.dumps(create,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CREATE TABS',create['tabs']); print('CREATE CARDS',len(create['cards']))
    for i,x in enumerate(create['cards']): print(i,x['text'],'|',x['rect'])
    page.goto('http://10.17.1.66:3001/create', wait_until='domcontentloaded'); page.wait_for_timeout(7000)
    page.evaluate("() => [...document.querySelectorAll('.purchase-gift-modal')].forEach(n=>n.remove())")
    with page.expect_file_chooser() as f: page.locator("text=Start from a Photo").first.click()
    f.value.set_files(str(ROOT/'test_images'/'无人脸.jpg'))
    page.wait_for_url('**/agent**',timeout=30000); page.wait_for_timeout(8000)
    page.get_by_role('button',name='Inspiration').first.click(); page.wait_for_timeout(5000)
    agent=extract(page)
    (SHOTS/'agent_inspire_cards.json').write_text(json.dumps(agent,ensure_ascii=False,indent=2),encoding='utf-8')
    print('AGENT TABS',agent['tabs']); print('AGENT CARDS',len(agent['cards']))
    for i,x in enumerate(agent['cards']): print(i,x['text'],'|',x['rect'])
    b.close()
