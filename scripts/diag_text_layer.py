"""Diagnostic script to find drafts tab and project cards."""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    ctx = b.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-US')
    pg = ctx.new_page()

    # Login
    pg.goto('http://10.17.1.66:3102', timeout=120000)
    pg.wait_for_timeout(5000)
    pg.get_by_text('Log in', exact=True).first.click()
    pg.wait_for_timeout(3000)
    pg.locator('input[type="email"]').fill('450832596@qq.com')
    pg.locator('input[placeholder="Verification Code"]').fill('123456')
    pg.evaluate('''()=>{var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}''')
    pg.wait_for_timeout(10000)
    pg.evaluate('''()=>{document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove();});}''')
    pg.wait_for_timeout(2000)

    # Go to project page
    pg.goto('http://10.17.1.66:3102/zh/project', timeout=60000)
    pg.wait_for_timeout(8000)
    pg.evaluate('''()=>{document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove();});}''')
    pg.wait_for_timeout(2000)

    # Find drafts tab using coordinator's selector
    sel = 'span.text-pc-normal-btn:has-text("草稿")'
    count = pg.locator(sel).count()
    print(f'Drafts tab count: {count}')
    if count > 0:
        box = pg.locator(sel).first.bounding_box()
        print(f'Drafts tab at ({box["x"]:.0f}, {box["y"]:.0f}) {box["width"]:.0f}x{box["height"]:.0f}')
        pg.locator(sel).first.click()
        pg.wait_for_timeout(3000)
        print('Clicked drafts tab')

    # Dismiss overlay
    pg.evaluate('''()=>{document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove();});}''')
    pg.wait_for_timeout(1000)

    # Find project cards
    cards = pg.evaluate('''()=>{var r=[];document.querySelectorAll("a,[class*='cursor-pointer']").forEach(function(e){var b=e.getBoundingClientRect();if(b.width>100&&b.height>100&&b.y>200){r.push({tg:e.tagName,x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),href:(e.getAttribute("href")||"").substring(0,80)});}});return r.slice(0,10);}''')
    print(f'Project cards after drafts switch: {json.dumps(cards, ensure_ascii=False)}')

    if cards:
        card = cards[0]
        pg.mouse.click(card['x']+card['w']/2, card['y']+card['h']/2)
        pg.wait_for_timeout(10000)
        pg.evaluate('''()=>{document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove();});}''')
        pg.wait_for_timeout(2000)
        print(f'After click URL: {pg.url}')

    pg.screenshot(path='data/debug/drafts_diag3.png')
    ctx.close()
    b.close()
