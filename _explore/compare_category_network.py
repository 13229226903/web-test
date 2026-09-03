from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(r'D:\Test\web-test')
TASK=ROOT/'artifacts'/'2026-08-27_pokecut_infinite_canvas_inspire_me'
SHOTS=TASK/'shots'
BASE='http://10.17.1.66:3001'

responses=[]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={'width':1920,'height':1080}, locale='en-US')
    page=ctx.new_page()
    def on_response(resp):
        try:
            url=resp.url
            if any(k in url.lower() for k in ['explore','template','style','inspire','aifilter']):
                ct=resp.headers.get('content-type','')
                body=''
                if 'json' in ct:
                    body=resp.text()
                responses.append({'status':resp.status,'url':url,'content_type':ct,'body':body[:20000]})
        except Exception as e:
            responses.append({'error':str(e),'url':getattr(resp,'url','')})
    page.on('response',on_response)
    page.goto(BASE+'/create',wait_until='domcontentloaded')
    page.wait_for_timeout(9000)
    page.evaluate("() => [...document.querySelectorAll('.purchase-gift-modal')].forEach(n=>n.remove())")
    # Locate exact category row near Explore cards.
    tabs=page.locator('button').filter(has_text='Trending')
    print('trending count',tabs.count())
    # scroll section into view
    page.evaluate("""() => {
      const cards=[...document.querySelectorAll('[data-explore-style-id]')];
      cards[0]?.scrollIntoView({block:'center'});
    }""")
    page.wait_for_timeout(1000)
    def snapshot(label):
        return page.evaluate("""(label) => {
          const vis=el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const cards=[...document.querySelectorAll('[data-explore-style-id]')].map(el=>{
            const r=el.getBoundingClientRect(); const img=el.querySelector('img');
            return {id:el.getAttribute('data-explore-style-id'),rect:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},src:img?img.src:null,visible:vis(el),text:el.innerText.trim().replace(/\\s+/g,' ')};
          });
          const buttons=[...document.querySelectorAll('button')].filter(vis).map(el=>({text:el.innerText.trim().replace(/\\s+/g,' '),rect:(()=>{const r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}})(),cls:el.className.toString()}));
          return {label,url:location.href,cards,buttons};
        }""", label)
    all_snap=[snapshot('create_default')]
    for tab in ['Trending','Festival','Face','Body','Hair','Creative Effects','Ecommerce','Anime gaming','Digital_art']:
        # use button at lowest y / within create page category row
        loc=page.locator('button',has_text=tab)
        n=loc.count()
        target=None
        for i in range(n):
            r=loc.nth(i).bounding_box()
            if r and r['y']>2000:
                target=loc.nth(i); break
        if not target:
            print('NO BUTTON',tab,n); continue
        try:
            target.scroll_into_view_if_needed(); page.wait_for_timeout(200)
            target.click(); page.wait_for_timeout(2000)
            all_snap.append(snapshot('create_'+tab))
            print('CLICKED',tab,'cards',len(all_snap[-1]['cards']),'visible',sum(c['visible'] for c in all_snap[-1]['cards']))
        except Exception as e:
            print('ERR',tab,e)
    # Agent path
    page.goto(BASE+'/create',wait_until='domcontentloaded'); page.wait_for_timeout(7000)
    page.evaluate("() => [...document.querySelectorAll('.purchase-gift-modal')].forEach(n=>n.remove())")
    with page.expect_file_chooser() as f:
        page.locator('text=Start from a Photo').first.click()
    f.value.set_files(str(ROOT/'test_images'/'无人脸.jpg'))
    page.wait_for_url('**/agent**',timeout=30000); page.wait_for_timeout(9000)
    page.get_by_role('button',name='Inspiration').first.click(); page.wait_for_timeout(6000)
    all_snap.append(snapshot('agent_default'))
    print('AGENT CARDS',len(all_snap[-1]['cards']),'visible',sum(c['visible'] for c in all_snap[-1]['cards']))
    for tab in ['Trending','Festival','Face','Body','Hair','Creative Effects','Ecommerce','Anime gaming','Digital_art']:
        loc=page.locator('button',has_text=tab)
        n=loc.count(); target=None
        for i in range(n):
            r=loc.nth(i).bounding_box()
            if r and r['y']<1000:
                target=loc.nth(i); break
        if not target:
            print('NO AGENT BUTTON',tab,n); continue
        try:
            target.click(); page.wait_for_timeout(2000)
            all_snap.append(snapshot('agent_'+tab))
            print('AGENT CLICKED',tab,'cards',len(all_snap[-1]['cards']),'visible',sum(c['visible'] for c in all_snap[-1]['cards']))
        except Exception as e: print('AGENT ERR',tab,e)
    (SHOTS/'compare_category_network_snapshots.json').write_text(json.dumps(all_snap,ensure_ascii=False,indent=2),encoding='utf-8')
    (SHOTS/'network_responses.json').write_text(json.dumps(responses,ensure_ascii=False,indent=2),encoding='utf-8')
    print('RESPONSES',len(responses))
    for r in responses:
        print('RES',r.get('status'),r.get('url'),len(r.get('body','')))
    b.close()
