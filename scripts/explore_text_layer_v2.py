"""
Pokecut 画布文字图层全参数探索 - v2: 通过项目页草稿进入(已验证可行)
"""
import os, sys, json, time, glob
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
OUT_DIR = r"D:\Test\web-test\artifacts\2026-07-23_pokecut_text_layer\shots"
SYNC_MD = r"D:\Test\web-test\artifacts\2026-07-23_pokecut_text_layer\sync.md"
os.makedirs(OUT_DIR, exist_ok=True)

for f in glob.glob(os.path.join(OUT_DIR, "*.png")):
    try: os.remove(f)
    except: pass

SHOT = [0]
def shot(page, name):
    SHOT[0] += 1
    fpath = os.path.join(OUT_DIR, f"{SHOT[0]:02d}_{name}.png")
    try:
        page.screenshot(path=fpath, full_page=False, timeout=30000)
        print(f"  [SHOT {SHOT[0]:02d}] {name}")
    except Exception as e:
        print(f"  [SHOT {SHOT[0]:02d}] {name} FAILED: {e}")
    return fpath

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def dismiss_all(page):
    try:
        page.evaluate("""()=>{
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o){
                var bg=window.getComputedStyle(o).backgroundColor;
                if(bg&&bg.includes('rgba'))o.remove();
            });
        }""")
        page.wait_for_timeout(1000)
    except: pass

def scan_region(page, xMin, xMax, yMin, yMax, label="area"):
    result = page.evaluate("""([xMin,xMax,yMin,yMax])=>{
        var items=[];
        document.querySelectorAll('*').forEach(function(el){
            var r=el.getBoundingClientRect();
            if(r.x>=xMin&&r.x<=xMax&&r.y>=yMin&&r.y<=yMax&&r.width>0&&r.height>0&&el.offsetWidth>0){
                var t=(el.textContent||'').trim();
                if(!t||t.length>200)return;
                var info={tg:el.tagName,tx:t.slice(0,120),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),ch:el.children.length};
                if(el.tagName==='INPUT'){info.it=el.getAttribute('type')||'';info.vl=(el.value||'').slice(0,40);info.mn=el.getAttribute('min')||'';info.mx=el.getAttribute('max')||'';}
                if(el.getAttribute('role'))info.rl=el.getAttribute('role');
                if(el.getAttribute('data-tool-id'))info.dt=el.getAttribute('data-tool-id');
                var cs=window.getComputedStyle(el);
                if(cs.cursor==='pointer')info.cursor='pointer';
                items.push(info);
            }
        });
        items.sort(function(a,b){return a.y-b.y||a.x-b.x;});
        return items;
    }""", [xMin, xMax, yMin, yMax])
    log(f"\n--- {label} ({len(result)} items) ---")
    for r in result:
        extra=[]
        if 'it' in r: extra.append(f"[{r['it']} v={r['vl']} min={r['mn']} max={r['mx']}]")
        if 'rl' in r: extra.append(f"role={r['rl']}")
        if 'dt' in r: extra.append(f"dt={r['dt']}")
        if 'cursor' in r: extra.append(f"clickable")
        log(f"  [{r['tg']}] ({r['x']},{r['y']}) {r['w']}x{r['h']} '{r['tx']}' {' '.join(extra)}")
    return result

FINDINGS = {}

def main():
    with sync_playwright() as p:
        # Headless mode for reliability (screenshots work better)
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        try:
            # ═════ 1. Login ═════
            log("=== 1. Login ===")
            pg.goto(BASE, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(5000)
            pg.get_by_text("Log in", exact=True).first.click()
            pg.wait_for_timeout(3000)
            pg.locator('input[type="email"]').fill("450832596@qq.com")
            pg.locator('input[placeholder="Verification Code"]').fill("123456")
            pg.evaluate("""()=>{var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            pg.wait_for_timeout(10000); dismiss_all(pg)
            log(f"Login done: {pg.url}")

            # ═════ 2. /zh/project → 找第一个项目 ═════
            log("=== 2. Project page -> find first project ===")
            pg.goto(f"{BASE}/zh/project", timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(10000); dismiss_all(pg)

            # 先扫描页面结构
            body = pg.evaluate("()=>document.body.innerText")
            log(f"Project page body (first 500): {body[:500]}")

            # 扫描顶部区域的所有tab/按钮
            top_area = scan_region(pg, 0, 1920, 0, 300, "PROJECT PAGE TOP")
            shot(pg, "project_page_top")

            # 找所有可点击的大卡片(100x100以上)
            cards = pg.evaluate("""()=>{
                var c=[];
                document.querySelectorAll('a,div[class*="cursor-pointer"],div[class*="card"],div[class*="project"]').forEach(function(el){
                    var b=el.getBoundingClientRect();
                    if(b.width>=60&&b.height>=60&&b.y>=150){
                        c.push({x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),tg:el.tagName,href:(el.getAttribute("href")||"").slice(0,60),cls:(el.className||"").slice(0,60)});
                    }
                });
                return c.slice(0,20);
            }""")
            log(f"All big cards/links: {json.dumps(cards, ensure_ascii=False)}")

            if not cards:
                # 尝试点击 "创建" 或 "新建项目" 来创建新项目
                log("No existing projects, trying to create one...")
                # 回到 create 页面上传
                pg.goto(f"{BASE}/zh/create", timeout=60000, wait_until="domcontentloaded")
                pg.wait_for_timeout(8000); dismiss_all(pg)
                log("Back to create page - will try upload flow")
                # fall through to upload approach...
                ctx.close(); b.close()
                log("Please run create-based flow instead")
                return

            card = cards[0]
            pg.mouse.click(card['x']+card['w']/2, card['y']+card['h']/2)
            pg.wait_for_timeout(15000); dismiss_all(pg)
            log(f"Editor URL: {pg.url}")
            shot(pg, "editor_loaded")

            # ═════ 3. 找 Canvas ═════
            log("=== 3. Find Canvas ===")
            canvas_box = None
            for attempt in range(20):
                cv = pg.evaluate("""()=>{
                    var cs=document.querySelectorAll('canvas');
                    for(var i=0;i<cs.length;i++){
                        if(cs[i].offsetWidth>50&&cs[i].offsetHeight>50){
                            var r=cs[i].getBoundingClientRect();
                            return {x:r.x,y:r.y,w:r.width,h:r.height};
                        }
                    }
                    return null;
                }""")
                if cv:
                    canvas_box = cv
                    log(f"Canvas found (attempt {attempt+1}): {json.dumps(canvas_box)}")
                    break
                pg.wait_for_timeout(3000)
                if attempt % 5 == 4:
                    log(f"  Attempt {attempt+1}/20...")
            else:
                log("ERROR: Canvas never appeared!")
                # 查看所有canvas状态
                all_canvas = pg.evaluate("""()=>{
                    var cs=document.querySelectorAll('canvas');
                    var r=[];
                    for(var i=0;i<cs.length;i++){
                        var b=cs[i].getBoundingClientRect();
                        r.push({i:i,x:b.x,y:b.y,w:b.width,h:b.height,ow:cs[i].offsetWidth,oh:cs[i].offsetHeight});
                    }
                    return r;
                }""")
                log(f"All canvas: {json.dumps(all_canvas)}")
                shot(pg, "no_canvas")
                ctx.close(); b.close(); return

            cx = canvas_box['x'] + canvas_box['w']/2
            cy = canvas_box['y'] + canvas_box['h']/2
            log(f"Canvas center: ({cx:.0f}, {cy:.0f})")

            # ═════ 4. 左侧工具扫描 + 点击文字工具 ═════
            log("=== 4. Left toolbar + Text tool ===")
            scan_region(pg, 0, 100, 350, 850, "LEFT TOOLBAR")

            text_tool = pg.locator('button[data-tool-id="text"]')
            if text_tool.count() == 0:
                log("ERROR: text tool not found!")
                ctx.close(); b.close(); return

            tb = text_tool.first.bounding_box()
            pg.mouse.click(tb['x']+tb['width']/2, tb['y']+tb['height']/2)
            pg.wait_for_timeout(2000)
            shot(pg, "text_tool_active")

            # 点 canvas 放文字
            pg.mouse.click(cx, cy); pg.wait_for_timeout(1500)
            pg.keyboard.type("Test"); pg.wait_for_timeout(1000)
            pg.keyboard.press("Enter"); pg.wait_for_timeout(2000)
            shot(pg, "text_placed")

            # ═════ 5. 重新激活选中文字 → 面板出现 ═════
            log("=== 5. Re-select text → right panel ===")
            img_tool = pg.locator('button[data-tool-id="image"]')
            if img_tool.count() > 0:
                ib = img_tool.first.bounding_box()
                pg.mouse.click(ib['x']+ib['width']/2, ib['y']+ib['height']/2)
                pg.wait_for_timeout(1000)
            pg.mouse.click(tb['x']+tb['width']/2, tb['y']+tb['height']/2)
            pg.wait_for_timeout(3000)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "text_selected")

            # ═════ 6. 扫描全页面 ═════
            log("\n" + "="*70)
            log("FULL PAGE SCAN AFTER TEXT SELECTED")
            log("="*70)
            scan_region(pg, 0, 1920, 0, 1080, "FULL PAGE")
            shot(pg, "full_page_baseline")

            # ═════ 7. 探索 Layer 1 顶部工具栏 ═════
            log("\n" + "="*70)
            log("LAYER 1: TOP TOOLBAR")
            log("="*70)
            top = scan_region(pg, 500, 1450, 380, 500, "TOP TOOLBAR")
            shot(pg, "top_toolbar")
            FINDINGS['top_toolbar'] = top

            # 7a. 字体按钮
            log("\n--- 7a. Font dropdown ---")
            font_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='字体'||t==='Font')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if font_btn:
                pg.mouse.click(font_btn['x'], font_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "font_dropdown")
                FINDINGS['font_dropdown'] = scan_region(pg, 400, 1400, 420, 900, "FONT DROPDOWN")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 7b. 样式按钮
            log("\n--- 7b. Style dropdown ---")
            style_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='样式'||t==='Style')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if style_btn:
                pg.mouse.click(style_btn['x'], style_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "style_dropdown")
                FINDINGS['style_dropdown'] = scan_region(pg, 400, 1400, 420, 900, "STYLE DROPDOWN")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 7c. 颜色
            log("\n--- 7c. Color picker ---")
            color_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='颜色'||t==='Color')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if color_btn:
                pg.mouse.click(color_btn['x'], color_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "color_picker")
                FINDINGS['color_picker'] = scan_region(pg, 400, 1400, 420, 900, "COLOR PICKER")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 7d. 对齐
            log("\n--- 7d. Alignment ---")
            align_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='对齐'||t==='Align')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if align_btn:
                pg.mouse.click(align_btn['x'], align_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "alignment")
                FINDINGS['alignment'] = scan_region(pg, 400, 1400, 420, 900, "ALIGNMENT")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 7e. 行距
            log("\n--- 7e. Line spacing ---")
            ls_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='行距'||t==='Line')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if ls_btn:
                pg.mouse.click(ls_btn['x'], ls_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "line_spacing")
                FINDINGS['line_spacing'] = scan_region(pg, 400, 1400, 420, 900, "LINE SPACING")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 7f. 字距
            log("\n--- 7f. Letter spacing ---")
            cs_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='字距'||t==='Letter')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if cs_btn:
                pg.mouse.click(cs_btn['x'], cs_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "letter_spacing")
                FINDINGS['letter_spacing'] = scan_region(pg, 400, 1400, 420, 900, "LETTER SPACING")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 7g + 7h 翻转
            for flabel, fname in [('水平翻转','flip_h'), ('垂直翻转','flip_v'), ('Flip H','flip_h'), ('Flip V','flip_v')]:
                hflip = pg.evaluate(f"""(function(){{
                    var btns=document.querySelectorAll('button');
                    for(var i=0;i<btns.length;i++){{
                        var t=btns[i].textContent.trim();
                        var r=btns[i].getBoundingClientRect();
                        if((t==='{flabel}')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){{
                            return {{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}};
                        }}
                    }}
                    return null;
                }})()""")
                if hflip:
                    pg.mouse.click(hflip['x'], hflip['y'])
                    pg.wait_for_timeout(1500)
                    shot(pg, fname)
                    log(f"Applied {flabel}")
                    pg.mouse.click(hflip['x'], hflip['y'])  # revert
                    pg.wait_for_timeout(1000)
                    break

            # 7i. 旋转
            log("\n--- 7i. Rotation ---")
            rot_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var t=btns[i].textContent.trim();
                    var r=btns[i].getBoundingClientRect();
                    if((t==='旋转'||t==='Rotation'||t==='Rotate')&&r.y>380&&r.y<500&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                    }
                }
                return null;
            }""")
            if rot_btn:
                pg.mouse.click(rot_btn['x'], rot_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "rotation")
                FINDINGS['rotation'] = scan_region(pg, 400, 1400, 420, 900, "ROTATION")
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # ═════ 8. Layer 2: 右侧属性面板 ═════
            log("\n" + "="*70)
            log("LAYER 2: RIGHT PROPERTY PANEL")
            log("="*70)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            scan_region(pg, 1050, 1550, 350, 950, "RIGHT PANEL")
            shot(pg, "right_panel")

            # 8a. 字体子面板
            log("\n--- 8a. Font sub-panel ---")
            font_expand = pg.evaluate("""()=>{
                var items=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    if(r.x>1470&&r.x<1550&&r.y>450&&r.y<650&&r.width>=8&&r.width<=24&&r.height>=8&&r.height<=24){
                        var p=el.parentElement;
                        items.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),parent:(p?p.textContent.trim().slice(0,50):'')});
                    }
                });
                return items;
            }""")
            log(f"Font expand arrows: {json.dumps(font_expand, ensure_ascii=False)}")

            if font_expand:
                fa = font_expand[0]
                pg.mouse.click(fa['x']+fa['w']/2, fa['y']+fa['h']/2)
                pg.wait_for_timeout(3000)
                shot(pg, "font_subpanel_open")
                FINDINGS['font_subpanel'] = scan_region(pg, 70, 550, 100, 1080, "FONT SUBPANEL")

                # 字体 grid
                font_grid = pg.evaluate("""()=>{
                    var f=[];
                    document.querySelectorAll('button').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>250&&r.y<550&&r.width>50&&r.height>50){
                            f.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),text:el.textContent.trim().slice(0,30)});
                        }
                    });
                    return f;
                }""")
                FINDINGS['font_grid'] = font_grid
                log(f"Font grid: {json.dumps(font_grid, ensure_ascii=False)}")

                # 点第二个字体试试
                if len(font_grid) > 1:
                    fg = font_grid[1]
                    pg.mouse.click(fg['x']+fg['w']/2, fg['y']+fg['h']/2)
                    pg.wait_for_timeout(1000)
                    log(f"Selected font: {fg['text']}")

                # 大小+不透明度滑块
                sliders = pg.evaluate("""()=>{
                    var s=[];
                    document.querySelectorAll('input[type="range"]').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>500&&r.y<900){
                            s.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),val:el.value,min:el.getAttribute('min'),max:el.getAttribute('max')});
                        }
                    });
                    return s;
                }""")
                FINDINGS['font_sliders'] = sliders
                log(f"Sliders: {json.dumps(sliders, ensure_ascii=False)}")

                # 调大小
                if len(sliders) > 0:
                    s = sliders[0]
                    pg.mouse.click(s['x']+s['w']*0.6, s['y']+s['h']/2)
                    pg.wait_for_timeout(500)
                if len(sliders) > 1:
                    s = sliders[1]
                    pg.mouse.click(s['x']+s['w']*0.7, s['y']+s['h']/2)
                    pg.wait_for_timeout(500)

                # 颜色
                colors = pg.evaluate("""()=>{
                    var c=[];
                    document.querySelectorAll('button,[class*="grid"] button').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>700&&r.y<1200&&r.width>=24&&r.height>=24&&r.width<60&&r.height<60){
                            c.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),bg:window.getComputedStyle(el).backgroundColor});
                        }
                    });
                    return c.slice(0,15);
                }""")
                FINDINGS['font_colors'] = colors
                log(f"Color blocks: {len(colors)}")

                if len(colors) > 2:
                    c = colors[2]
                    pg.mouse.click(c['x']+c['w']/2, c['y']+c['h']/2)
                    pg.wait_for_timeout(500)

                # Apply
                pg.evaluate("""()=>{
                    var btns=document.querySelectorAll('button');
                    for(var i=0;i<btns.length;i++){
                        var t=btns[i].textContent.trim();
                        if((t==='应用'||t==='Apply')&&btns[i].offsetWidth>50){
                            btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                            return;
                        }
                    }
                }""")
                pg.wait_for_timeout(2000)
                shot(pg, "font_subpanel_adjusted")

            # ═════ 9. 样式子面板 ═════
            log("\n" + "="*70)
            log("LAYER 2: STYLE SUB-PANEL")
            log("="*70)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)

            style_expand = pg.evaluate("""()=>{
                var items=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    if(r.x>1470&&r.x<1550&&r.y>550&&r.y<800&&r.width>=8&&r.width<=24&&r.height>=8&&r.height<=24){
                        var p=el.parentElement;
                        items.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),parent:(p?p.textContent.trim().slice(0,50):'')});
                    }
                });
                return items;
            }""")
            log(f"Style expand arrows: {json.dumps(style_expand, ensure_ascii=False)}")

            if style_expand:
                sa = style_expand[-1] if len(style_expand) > 1 else style_expand[0]
                pg.mouse.click(sa['x']+sa['w']/2, sa['y']+sa['h']/2)
                pg.wait_for_timeout(3000)
                shot(pg, "style_subpanel_open")
                FINDINGS['style_subpanel'] = scan_region(pg, 70, 550, 100, 1080, "STYLE SUBPANEL")

                # 找所有控件
                style_ctrl = pg.evaluate("""()=>{
                    var c=[];
                    document.querySelectorAll('input,button,[role="switch"],[role="slider"],[role="checkbox"]').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>100&&r.y<1100&&r.width>0&&r.height>0){
                            c.push({tg:el.tagName,tx:(el.textContent||'').trim().slice(0,40),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),it:el.getAttribute('type')||'',vl:(el.value||'').slice(0,20),mn:el.getAttribute('min')||'',mx:el.getAttribute('max')||''});
                        }
                    });
                    return c;
                }""")
                FINDINGS['style_controls'] = style_ctrl
                log(f"Style controls: {json.dumps(style_ctrl, ensure_ascii=False)}")

                # Toggle switches
                toggles = pg.evaluate("""()=>{
                    var t=[];
                    document.querySelectorAll('*').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>150&&r.x<500&&r.y>200&&r.y<1000&&r.width>=30&&r.width<=60&&r.height>=15&&r.height<=30){
                            var cls=(el.className||'');
                            if(typeof cls==='string'&&(cls.includes('rounded-full')||cls.includes('toggle')||cls.includes('switch'))){
                                t.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
                            }
                        }
                    });
                    return t;
                }""")
                log(f"Toggles: {json.dumps(toggles)}")
                for i, tgl in enumerate(toggles[:5]):
                    pg.mouse.click(tgl['x']+tgl['w']/2, tgl['y']+tgl['h']/2)
                    pg.wait_for_timeout(1000)
                    shot(pg, f"style_toggle_{i+1}")

                # 滚动看完整内容
                pg.evaluate("""()=>{
                    var all=document.querySelectorAll('*');
                    for(var i=0;i<all.length;i++){
                        var r=all[i].getBoundingClientRect();
                        if(r.x>80&&r.x<550&&r.width>200&&r.height>200&&all[i].scrollHeight>all[i].clientHeight+10){
                            all[i].scrollTop=all[i].scrollHeight;
                            return;
                        }
                    }
                }""")
                pg.wait_for_timeout(1500)
                shot(pg, "style_subpanel_scrolled")
                FINDINGS['style_scrolled'] = scan_region(pg, 70, 550, 100, 1080, "STYLE SCROLLED")

                # 找颜色和滑块
                style_colors = pg.evaluate("""()=>{
                    var c=[];
                    document.querySelectorAll('*').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>200&&r.y<1200&&r.width>=24&&r.height>=24&&r.width<60&&r.height<60){
                            var bg=window.getComputedStyle(el).backgroundColor;
                            if(bg&&bg!=='rgba(0, 0, 0, 0)'&&bg!=='rgba(255, 255, 255, 1)'){
                                c.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),bg:bg,tg:el.tagName});
                            }
                        }
                    });
                    return c;
                }""")
                FINDINGS['style_colors'] = style_colors
                log(f"Style colors: {len(style_colors)}")

                # Apply
                pg.evaluate("""()=>{
                    var btns=document.querySelectorAll('button');
                    for(var i=0;i<btns.length;i++){
                        var t=btns[i].textContent.trim();
                        if((t==='应用'||t==='Apply')&&btns[i].offsetWidth>50){
                            btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                            return;
                        }
                    }
                }""")
                pg.wait_for_timeout(2000)

            # ═════ 10. Layer 2: 调整大小 / 图层按钮 ═════
            log("\n" + "="*70)
            log("RESIZE & LAYER BUTTONS")
            log("="*70)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)

            for bname, blabel in [('调整大小','resize'), ('Resize','resize'), ('图层','layer'), ('Layers','layer')]:
                btn = pg.evaluate(f"""(function(){{
                    var btns=document.querySelectorAll('button');
                    for(var i=0;i<btns.length;i++){{
                        var t=btns[i].textContent.trim();
                        var r=btns[i].getBoundingClientRect();
                        if((t==='{bname}')&&r.x>1050&&r.y>350&&r.y<550){{
                            return {{x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)}};
                        }}
                    }}
                    return null;
                }})()""")
                if btn:
                    pg.mouse.click(btn['x'], btn['y']); pg.wait_for_timeout(2000)
                    shot(pg, blabel)
                    FINDINGS[blabel] = scan_region(pg, 1050, 1920, 350, 900, blabel.upper())
                    pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
                    break

            # ═════ 11. 最终截图 ═════
            log("\n=== FINAL STATE ===")
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "final_all_adjusted")

            # ═════ 12. Body text ═════
            body = pg.evaluate("()=>document.body.innerText")
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            log(f"\n=== BODY TEXT EXCERPT ({len(lines)} lines) ===")
            for l in lines[:80]:
                log(f"  {l}")

            log(f"\n=== DONE! Total screenshots: {SHOT[0]} ===")

            # ═════ 13. 写出 sync.md ═════
            write_sync_md()

        except Exception as e:
            import traceback
            log(f"ERROR: {e}")
            traceback.print_exc()
            try: shot(pg, "ERROR")
            except: pass
        finally:
            ctx.close()
            b.close()


def write_sync_md():
    md = []
    md.append("---")
    md.append("task_id: 2026-07-23_pokecut_text_layer")
    md.append("agent: page-map-sync")
    md.append("status: completed")
    md.append("inputs:")
    md.append("  - PROJECT.md")
    md.append("  - rule.md")
    md.append("  - page_map/pokecut/create_ai_tools.yaml")
    md.append("outputs:")
    md.append("  scanned_pages:")
    md.append("    - /zh/project (项目列表 → 草稿)")
    md.append("    - /zh/agent?pid=... (画布编辑器)")
    md.append("  screenshots_dir: artifacts/2026-07-23_pokecut_text_layer/shots/")
    md.append(f"  total_screenshots: {SHOT[0]}")
    md.append("next_agent: test-case-design")
    md.append("---")
    md.append("")
    md.append("# Pokecut 画布文字图层 — 全参数探索 (v2)")
    md.append("")
    md.append("## 导航流程")
    md.append("```")
    md.append("登录 → /zh/project → 草稿Tab → 点击第一个项目")
    md.append("→ /zh/agent → 文字工具 → Canvas点击 → 输入文字")
    md.append("→ 切换工具再切回 → Canvas选中文字 → 面板出现")
    md.append("```")
    md.append("")
    md.append("## Layer 1: 顶部工具栏")
    md.append("| 参数 | 类型 | 截图 |")
    md.append("|------|------|------|")
    md.append("| 字体 | button → dropdown | font_dropdown |")
    md.append("| 样式 | button → dropdown | style_dropdown |")
    md.append("| 颜色 | button → picker | color_picker |")
    md.append("| 对齐 | button → dropdown | alignment |")
    md.append("| 行距 | button → slider | line_spacing |")
    md.append("| 字距 | button → slider | letter_spacing |")
    md.append("| 水平翻转 | button (toggle) | flip_h |")
    md.append("| 垂直翻转 | button (toggle) | flip_v |")
    md.append("| 旋转 | button → dropdown | rotation |")
    md.append("| 删除 | button (red) | — |")
    md.append("")

    # Add findings details
    for key, val in FINDINGS.items():
        if isinstance(val, list) and len(val) > 0:
            md.append(f"### {key}")
            md.append(f"({len(val)} elements)")
            for v in val[:20]:
                md.append(f"- [{v.get('tg','')}] ({v.get('x','')},{v.get('y','')}) {v.get('w','')}x{v.get('h','')} '{v.get('tx','')}'")
            md.append("")

    md.append("## 截图索引")
    md.append("")
    md.append("| # | 名称 |")
    md.append("|---|------|")
    for i in range(1, SHOT[0]+1):
        md.append(f"| {i:02d} | screenshot |")
    md.append("")

    with open(SYNC_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"\nsync.md written to: {SYNC_MD}")


if __name__ == "__main__":
    main()

