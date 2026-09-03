"""Debug: 找到每个页面的正确 CTA 按钮。"""
from playwright.sync_api import sync_playwright
import os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')
imgs=sorted(glob.glob(os.path.join(os.path.dirname(__file__),'..','test_images','*')),key=lambda f:os.path.getsize(f))
img=os.path.abspath(imgs[0])

pages=['/tools/add-a-person-to-a-photo','/batch-edit','/ai-background','/ai-image-generator','/image-to-image-ai','/collage-maker']

with sync_playwright() as p:
    b=p.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':1920,'height':1080},locale='en-US');page=ctx.new_page()
    page.goto('http://10.17.1.66:3002',timeout=30000);page.wait_for_timeout(5000)
    page.get_by_text('Log in',exact=True).first.click();page.wait_for_timeout(3000)
    page.locator('input[type=\"email\"]').fill('450832596@qq.com')
    page.locator('input[placeholder=\"Verification Code\"]').fill('123456')
    page.evaluate('''()=>{var b=document.querySelectorAll(\"button\");for(var i=0;i<b.length;i++){if(b[i].textContent.trim()===\"Log in\"&&b[i].offsetWidth>200){b[i].dispatchEvent(new MouseEvent(\"click\",{bubbles:true,cancelable:true}));break;}}}''')
    page.wait_for_timeout(10000)
    print('[OK] Logged in')

    for path in pages:
        page.goto(f'http://10.17.1.66:3002{path}',timeout=120000)
        try:page.wait_for_load_state('networkidle',timeout=30000)
        except:pass
        page.wait_for_timeout(3000)
        page.evaluate('()=>{document.querySelectorAll(\"div[class*=fixed]\").forEach(o=>{var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes(\"rgba\")&&(bg.includes(\"0.3\")||bg.includes(\"0.5\")))o.remove()})}')
        page.wait_for_timeout(1000)
        print(f'\n=== {path} ===')
        btns=page.evaluate('''()=>{var all=document.querySelectorAll(\"button\");var r=[];for(var i=0;i<all.length;i++){var rect=all[i].getBoundingClientRect();var t=all[i].textContent.trim();if(t&&rect.y>100&&rect.width>20)r.push({text:t.substring(0,50),y:Math.round(rect.y),w:Math.round(rect.width)});}r.sort(function(a,b){return a.y-b.y});return r}''')
        for b in btns:print(f'  y={b[\"y\"]} w={b[\"w\"]} \"{b[\"text\"]}\"')
        for b in btns[:5]:
            try:
                with page.expect_file_chooser(timeout=5000) as fc:
                    page.evaluate('''(text,w)=>{var btns=document.querySelectorAll(\"button\");for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()===text&&btns[i].offsetWidth===w){btns[i].dispatchEvent(new MouseEvent(\"click\",{bubbles:true,cancelable:true}));return;}}}''',b['text'],b['w'])
                fc.value.set_files(img);page.wait_for_timeout(8000)
                print(f'  FILE CHOOSER: \"{b[\"text\"]}\" -> {page.url}')
                break
            except:pass
        else:
            for b in btns[:3]:
                try:
                    prev=page.url;page.locator(f'button:has-text(\"{b[\"text\"]}\"):visible').first.click();page.wait_for_timeout(5000)
                    if page.url!=prev:print(f'  NAVIGATE: \"{b[\"text\"]}\" -> {page.url}');break
                except:pass
    b.close()
