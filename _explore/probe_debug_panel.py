import sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(r'D:\Test\web-test')
OUT=ROOT/'artifacts'/'2026-08-26_pokecut_text_enhancer'
URL='http://10.17.1.66:3001/tools/ai-image-text-enhancer'
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.goto(URL, wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(8000)
    before=page.locator('body').inner_text()
    # find elements whose visible text contains DEBUG or 预部署
    info=page.evaluate('''() => {
      const vis=el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
      const out=[];
      document.querySelectorAll('body *').forEach(el=>{
        if(!vis(el))return;
        const text=(el.innerText||el.textContent||'').replace(/\\s+/g,' ').trim();
        if(!/debug|预部署|deploy/i.test(text)) return;
        const r=el.getBoundingClientRect();
        out.push({tag:el.tagName,text:text.slice(0,200),cls:String(el.className).slice(0,150),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
      });
      return out;
    }''')
    print('BEFORE SNAPSHOT')
    print(before[:3000])
    print('\nMATCHES BEFORE')
    for row in info[:100]: print(row)
    # click smallest element containing DEBUG
    candidates=page.locator('text=DEBUG')
    print('debug candidate count',candidates.count())
    if candidates.count()>0:
        try:
            cands=candidates.all()
            smallest=min(cands,key=lambda loc: loc.bounding_box() and loc.bounding_box()['width']*loc.bounding_box()['height'] or 1e9)
            smallest.click(timeout=5000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print('click error',repr(e))
    after=page.locator('body').inner_text()
    info2=page.evaluate('''() => {
      const vis=el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
      const out=[];
      document.querySelectorAll('body *').forEach(el=>{
        if(!vis(el))return;
        const text=(el.innerText||el.textContent||'').replace(/\\s+/g,' ').trim();
        if(!/debug|预部署|deploy/i.test(text)) return;
        const r=el.getBoundingClientRect();
        out.push({tag:el.tagName,text:text.slice(0,200),cls:String(el.className).slice(0,150),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
      });
      return out;
    }''')
    page.screenshot(path=str(OUT/'debug_panel_after_click.png'), full_page=False)
    print('\nAFTER SNAPSHOT')
    print(after[:5000])
    print('\nMATCHES AFTER')
    for row in info2[:100]: print(row)
    browser.close()
