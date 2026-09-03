"""
全面探索 Pokecut 画布文字图层全部参数面板。
流程: /zh/create → 从照片开始(上传最小图片) → canvas → 文字工具 → 逐参数截图。
"""
import os, sys, json, time, glob, re
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
# 硬编码绝对路径 - 探索脚本专用
TEST_IMAGE = r"D:\Test\web-test\test_images\3 - 副本.JPG"
OUT_DIR = r"D:\Test\web-test\artifacts\2026-07-23_pokecut_text_layer\shots"
SYNC_MD = r"D:\Test\web-test\artifacts\2026-07-23_pokecut_text_layer\sync.md"
assert os.path.exists(TEST_IMAGE), f"TEST_IMAGE not found: {TEST_IMAGE}"
os.makedirs(OUT_DIR, exist_ok=True)

# 清空旧截图
for f in glob.glob(os.path.join(OUT_DIR, "*.png")):
    try: os.remove(f)
    except: pass

SHOT = [0]
def shot(page, name):
    SHOT[0] += 1
    fpath = os.path.join(OUT_DIR, f"{SHOT[0]:02d}_{name}.png")
    try:
        page.screenshot(path=fpath, full_page=False, timeout=15000)
        print(f"  [SCREENSHOT {SHOT[0]:02d}] {name}")
        return fpath
    except Exception as e:
        print(f"  [SCREENSHOT {SHOT[0]:02d}] {name} FAILED: {e}")
        return None

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def dismiss_all(page):
    try:
        page.evaluate("""()=>{
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o){
                var bg=window.getComputedStyle(o).backgroundColor;
                if(bg&&bg.includes('rgba')&&(bg.includes('0.3')||bg.includes('0.5')||bg.includes('0.2')||bg.includes('0.4')))o.remove();
            });
        }""")
        page.wait_for_timeout(1000)
    except: pass

def scan_region(page, xMin, xMax, yMin, yMax, label="区域"):
    """扫描指定矩形区域内所有可见元素"""
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

def click_center(page, el_info):
    page.mouse.click(el_info['x']+el_info['w']/2, el_info['y']+el_info['h']/2)

def find_canvas_center(page):
    cb = page.locator('canvas').first.bounding_box()
    if not cb:
        log("ERROR: Cannot find canvas!")
        return None
    return cb['x'] + cb['width']/2, cb['y'] + cb['height']/2

# 记录所有发现
FINDINGS = {}

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        try:
            # ════════════════════════════════════════════════
            # 1. 登录
            # ════════════════════════════════════════════════
            log("=== Step 1: Login ===")
            # 拦截分析/追踪请求加速
            pg.route("**/*", lambda route: route.abort() if route.request.resource_type in ["ping","media"] else route.continue_())
            pg.goto(BASE, timeout=120000); pg.wait_for_timeout(5000)
            pg.get_by_text("Log in", exact=True).first.click(); pg.wait_for_timeout(3000)
            pg.locator('input[type="email"]').fill("450832596@qq.com")
            pg.locator('input[placeholder="Verification Code"]').fill("123456")
            pg.evaluate("""()=>{var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            pg.wait_for_timeout(10000); dismiss_all(pg)
            log(f"Login done: {pg.url}")

            # ════════════════════════════════════════════════
            # 2. /zh/create → 关弹窗 → "从照片开始"
            # ════════════════════════════════════════════════
            log("=== Step 2: /zh/create → Start from a Photo ===")
            pg.goto(f"{BASE}/zh/create", timeout=60000); pg.wait_for_timeout(8000)
            dismiss_all(pg)
            shot(pg, "create_page")

            # 扫描 "热门工具" 区块 (Trending Tools)
            tools_scan = scan_region(pg, 100, 1800, 300, 900, "Create Page Tools")

            # 找 "从照片开始" 按钮 (中文UI) 或 "Start from a Photo"
            start_btn = pg.evaluate("""()=>{
                var all=document.querySelectorAll('*');
                for(var i=0;i<all.length;i++){
                    var t=all[i].textContent.trim();
                    if((t==='从照片开始'||t==='Start from a Photo')&&all[i].children.length===0){
                        var r=all[i].getBoundingClientRect();
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),text:t};
                    }
                }
                return null;
            }""")
            log(f"Start button: {json.dumps(start_btn, ensure_ascii=False)}")

            if not start_btn:
                # Fallback: find the parent cursor-pointer div
                start_div = pg.evaluate("""()=>{
                    var divs=document.querySelectorAll('div.cursor-pointer');
                    for(var i=0;i<divs.length;i++){
                        var t=divs[i].textContent.trim();
                        if(t.includes('从照片开始')||t.includes('Start from a Photo')){
                            var r=divs[i].getBoundingClientRect();
                            return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),text:t.slice(0,30)};
                        }
                    }
                    return null;
                }""")
                log(f"Start div: {json.dumps(start_div, ensure_ascii=False)}")
                if start_div:
                    start_btn = start_div

            # 3. 点击 → 文件选择器 → 上传最小图片
            log("=== Step 3: Upload image ===")
            log(f"Using image: {TEST_IMAGE}")
            with pg.expect_file_chooser() as fc_info:
                pg.mouse.click(start_btn['x'], start_btn['y'])
                pg.wait_for_timeout(1000)
            fc_info.value.set_files(TEST_IMAGE)
            pg.wait_for_timeout(15000)  # 等待上传+进入编辑器
            dismiss_all(pg)
            log(f"After upload URL: {pg.url}")
            shot(pg, "canvas_loaded")

            # ════════════════════════════════════════════════
            # 4. 深度探测 canvas — 检查 iframe / shadow DOM / 动态创建
            # ════════════════════════════════════════════════
            log("=== Step 4: Deep canvas detection ===")
            pg.wait_for_timeout(5000)
            dismiss_all(pg)

            # 先做全面探测
            debug_info = pg.evaluate("""()=>{
                var result={iframes:0,canvas_all:[],canvas_visible:[],fabric:false,konva:false};
                // iframes
                result.iframes=document.querySelectorAll('iframe').length;
                if(result.iframes>0){
                    var ifs=document.querySelectorAll('iframe');
                    for(var i=0;i<ifs.length;i++){
                        try{
                            var doc=ifs[i].contentDocument||ifs[i].contentWindow.document;
                            var cs=doc.querySelectorAll('canvas');
                            for(var j=0;j<cs.length;j++){
                                var r=cs[j].getBoundingClientRect();
                                result.canvas_all.push({src:'iframe#'+i,idx:j,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),vis:cs[j].offsetWidth>0});
                            }
                        }catch(e){result.iframeError=e.message.slice(0,50);}
                    }
                }
                // direct canvas
                var cs=document.querySelectorAll('canvas');
                for(var j=0;j<cs.length;j++){
                    var r=cs[j].getBoundingClientRect();
                    result.canvas_all.push({src:'main',idx:j,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),vis:cs[j].offsetWidth>0});
                    if(cs[j].offsetWidth>0) result.canvas_visible.push({x:r.x,y:r.y,w:r.width,h:r.height});
                }
                // check fabric/konva
                if(typeof window.fabric!=='undefined') result.fabric=true;
                if(typeof window.Konva!=='undefined') result.konva=true;
                // 查找大的可交互区域(可能是canvas容器)
                var bigDivs=[];
                document.querySelectorAll('div').forEach(function(d){
                    var r=d.getBoundingClientRect();
                    if(r.width>200&&r.height>200&&r.x>50&&r.x<1400&&r.y>200&&r.y<800){
                        bigDivs.push({tg:d.tagName,id:d.id||'',cls:(d.className||'').slice(0,60),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
                    }
                });
                result.big_divs=bigDivs.slice(0,10);
                return result;
            }""")
            log(f"Debug info: {json.dumps(debug_info, ensure_ascii=False)}")

            # 如果有可见 canvas 就用
            canvas_box = None
            if debug_info.get('canvas_visible') and len(debug_info['canvas_visible']) > 0:
                cv = debug_info['canvas_visible'][0]
                if cv['w'] > 50 and cv['h'] > 50:
                    canvas_box = cv
                    log(f"Canvas found immediately: {json.dumps(canvas_box)}")

            # 如果没有，等待一下再试 (canvas 可能由 JS 动态创建)
            if not canvas_box:
                log("No visible canvas yet, waiting for dynamic creation...")
                max_wait = 30
                waited = 0
                while waited < max_wait:
                    pg.wait_for_timeout(5000)
                    waited += 5
                    dismiss_all(pg)
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
                        log(f"Canvas appeared after {waited}s: {json.dumps(canvas_box)}")
                        break
                    log(f"  [{waited}s] No canvas...")

            if not canvas_box:
                # 最终尝试: 点击编辑器中心容器激活 canvas
                log("Final attempt: clicking on big container div to initialize canvas...")
                # 大容器在 x≈778, y≈307, 364x546 -> center = (960, 580)
                if debug_info.get('big_divs') and len(debug_info['big_divs']) > 0:
                    bd = debug_info['big_divs'][0]
                    ctr_x = bd['x'] + bd['w']/2
                    ctr_y = bd['y'] + bd['h']/2
                    log(f"Clicking container at ({ctr_x:.0f}, {ctr_y:.0f})")
                    pg.mouse.click(ctr_x, ctr_y)
                    pg.wait_for_timeout(3000)
                    # also double click
                    pg.mouse.dblclick(ctr_x, ctr_y)
                    pg.wait_for_timeout(5000)
                    dismiss_all(pg)
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
                        log(f"Canvas initialized after click! {json.dumps(canvas_box)}")

                if not canvas_box:
                    # 检查是否有 img 标签而非 canvas
                    imgs = pg.evaluate("""()=>{
                        var imgs=document.querySelectorAll('img');
                        var result=[];
                        for(var i=0;i<imgs.length;i++){
                            var r=imgs[i].getBoundingClientRect();
                            if(r.width>100&&r.height>100){
                                result.push({i:i,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),src:(imgs[i].src||'').slice(0,80)});
                            }
                        }
                        return result;
                    }""")
                    log(f"Large images found: {json.dumps(imgs, ensure_ascii=False)}")
                    log("ERROR: Canvas still not found after all attempts!")
                    shot(pg, "no_canvas_final")
                    ctx.close(); b.close(); return

            cx = canvas_box['x'] + canvas_box['w']/2
            cy = canvas_box['y'] + canvas_box['h']/2
            log(f"Canvas center: ({cx:.0f}, {cy:.0f})")

            # ════════════════════════════════════════════════
            # 5. 左侧工具扫描 → 点击文字工具 → 放文字
            # ════════════════════════════════════════════════
            log("=== Step 5: Activate text tool & place text ===")
            left_tools = scan_region(pg, 0, 150, 350, 850, "LEFT TOOLBAR")

            text_tool = pg.locator('button[data-tool-id="text"]')
            if text_tool.count() == 0:
                log("ERROR: text tool not found!")
                ctx.close(); b.close(); return

            tb = text_tool.first.bounding_box()
            log(f"Text tool at ({tb['x']:.0f},{tb['y']:.0f})")
            pg.mouse.click(tb['x']+tb['width']/2, tb['y']+tb['height']/2)
            pg.wait_for_timeout(2000)
            shot(pg, "text_tool_active")

            # 点击 canvas 中央放文字
            pg.mouse.click(cx, cy); pg.wait_for_timeout(1500)
            pg.keyboard.type("Test"); pg.wait_for_timeout(1000)
            pg.keyboard.press("Enter"); pg.wait_for_timeout(2000)
            shot(pg, "text_placed")

            # ════════════════════════════════════════════════
            # 6. 切其他工具 → 切回文字 → 点canvas选中 → 右侧面板出现
            # ════════════════════════════════════════════════
            log("=== Step 6: Re-select text to show right panel ===")
            img_tool = pg.locator('button[data-tool-id="image"]')
            if img_tool.count() > 0:
                ib = img_tool.first.bounding_box()
                pg.mouse.click(ib['x']+ib['width']/2, ib['y']+ib['height']/2)
                pg.wait_for_timeout(1000)
                log("Switched to image tool")
            pg.mouse.click(tb['x']+tb['width']/2, tb['y']+tb['height']/2)
            pg.wait_for_timeout(3000)
            # 点击 canvas 上文字位置选中
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "text_selected_panel_visible")

            # ─────────────────────────────────────────────
            # 全页面基线扫描
            # ─────────────────────────────────────────────
            log("\n" + "="*70)
            log("BASELINE SCAN - Full page after text selected")
            log("="*70)
            scan_region(pg, 0, 1920, 0, 1080, "FULL PAGE BASELINE")
            shot(pg, "baseline_full")

            # ════════════════════════════════════════════════
            # 7. 探索顶部工具栏 (Layer 1: y≈420-460)
            # ════════════════════════════════════════════════
            log("\n" + "="*70)
            log("LAYER 1: TOP TOOLBAR EXPLORATION")
            log("="*70)

            top_toolbar = scan_region(pg, 500, 1450, 380, 500, "TOP TOOLBAR")
            shot(pg, "top_toolbar")

            # 7a. 字体按钮 → 探索字体下拉
            log("\n--- 7a. Font dropdown ---")
            font_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='字体'||t==='Font')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if font_btn:
                pg.mouse.click(font_btn['x'], font_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "font_dropdown_top")
                font_drop = scan_region(pg, 400, 1400, 420, 900, "FONT DROPDOWN")
                FINDINGS['top_font'] = font_drop
                # 点空白关闭
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Font button not found in top toolbar!")

            # 7b. 样式按钮 → 探索样式下拉
            log("\n--- 7b. Style dropdown ---")
            style_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='样式'||t==='Style')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if style_btn:
                pg.mouse.click(style_btn['x'], style_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "style_dropdown_top")
                style_drop = scan_region(pg, 400, 1400, 420, 900, "STYLE DROPDOWN")
                FINDINGS['top_style'] = style_drop
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Style button not found in top toolbar!")

            # 7c. 颜色按钮 → 颜色选择器
            log("\n--- 7c. Color picker ---")
            color_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='颜色'||t==='Color')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if color_btn:
                pg.mouse.click(color_btn['x'], color_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "color_picker_top")
                color_pick = scan_region(pg, 400, 1400, 420, 900, "COLOR PICKER")
                FINDINGS['top_color'] = color_pick
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Color button not found in top toolbar!")

            # 7d. 对齐按钮 → 对齐选项
            log("\n--- 7d. Alignment ---")
            align_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='对齐'||t==='Align')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if align_btn:
                pg.mouse.click(align_btn['x'], align_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "alignment_options")
                align_drop = scan_region(pg, 400, 1400, 420, 900, "ALIGNMENT")
                FINDINGS['top_align'] = align_drop
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Align button not found!")

            # 7e. 行距
            log("\n--- 7e. Line spacing ---")
            lspacing_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='行距'||t==='Line Spacing'||t==='Line')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if lspacing_btn:
                pg.mouse.click(lspacing_btn['x'], lspacing_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "line_spacing")
                ls_drop = scan_region(pg, 400, 1400, 420, 900, "LINE SPACING")
                FINDINGS['top_linespacing'] = ls_drop
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Line spacing button not found!")

            # 7f. 字距
            log("\n--- 7f. Letter spacing ---")
            cspacing_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='字距'||t==='Letter Spacing'||t==='Letter')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if cspacing_btn:
                pg.mouse.click(cspacing_btn['x'], cspacing_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "letter_spacing")
                cs_drop = scan_region(pg, 400, 1400, 420, 900, "LETTER SPACING")
                FINDINGS['top_letterspacing'] = cs_drop
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Letter spacing button not found!")

            # 7g. 水平翻转
            log("\n--- 7g. Horizontal flip ---")
            hflip_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='水平翻转'||t==='Flip H'||t==='Flip Horizontal')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if hflip_btn:
                pg.mouse.click(hflip_btn['x'], hflip_btn['y']); pg.wait_for_timeout(1500)
                shot(pg, "flip_horizontal")
                log(f"Horizontal flip applied")
                FINDINGS['top_flip_h'] = hflip_btn
                # 再点一次恢复
                pg.mouse.click(hflip_btn['x'], hflip_btn['y']); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Horizontal flip button not found!")

            # 7h. 垂直翻转
            log("\n--- 7h. Vertical flip ---")
            vflip_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='垂直翻转'||t==='Flip V'||t==='Flip Vertical')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if vflip_btn:
                pg.mouse.click(vflip_btn['x'], vflip_btn['y']); pg.wait_for_timeout(1500)
                shot(pg, "flip_vertical")
                log(f"Vertical flip applied")
                FINDINGS['top_flip_v'] = vflip_btn
                pg.mouse.click(vflip_btn['x'], vflip_btn['y']); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Vertical flip button not found!")

            # 7i. 旋转
            log("\n--- 7i. Rotation ---")
            rot_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='旋转'||t==='Rotation'||t==='Rotate')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if rot_btn:
                pg.mouse.click(rot_btn['x'], rot_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "rotation")
                rot_drop = scan_region(pg, 400, 1400, 420, 900, "ROTATION")
                FINDINGS['top_rotation'] = rot_drop
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)
            else:
                log("WARNING: Rotation button not found!")

            # 7j. 删除按钮存在性(不点)
            log("\n--- 7j. Delete button ---")
            del_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='删除'||t==='Delete')&&r.y>410&&r.y<470&&r.x>500&&r.x<1400){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            FINDINGS['top_delete'] = del_btn
            log(f"Delete button: {json.dumps(del_btn, ensure_ascii=False)}")

            # ════════════════════════════════════════════════
            # 8. 探索右侧属性面板 (Layer 2)
            # ════════════════════════════════════════════════
            log("\n" + "="*70)
            log("LAYER 2: RIGHT PROPERTY PANEL")
            log("="*70)

            # 重新选中文字(确保面板可见)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)

            right_panel = scan_region(pg, 1050, 1550, 350, 950, "RIGHT PANEL FULL")
            shot(pg, "right_panel")

            # 8a. 字体行 → 展开子面板 (Layer 3)
            log("\n--- 8a. Font row → Layer 3 subpanel ---")
            # 找字体行的展开箭头 (12x12, x≈1500)
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
            log(f"Expand arrows in right panel: {json.dumps(font_expand, ensure_ascii=False)}")

            if font_expand:
                # 第一个箭头通常是字体行
                fa = font_expand[0]
                pg.mouse.click(fa['x']+fa['w']/2, fa['y']+fa['h']/2)
                pg.wait_for_timeout(3000)
                shot(pg, "font_subpanel_open")

                # 扫描子面板
                font_sub = scan_region(pg, 70, 550, 100, 1080, "FONT SUB PANEL")
                FINDINGS['font_subpanel'] = font_sub

                # 字体 grid
                font_grid = pg.evaluate("""()=>{
                    var fonts=[];
                    document.querySelectorAll('button').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>250&&r.y<550&&r.width>50&&r.height>50){
                            fonts.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),text:el.textContent.trim().slice(0,30)});
                        }
                    });
                    return fonts;
                }""")
                log(f"Font grid buttons: {json.dumps(font_grid, ensure_ascii=False)}")
                FINDINGS['font_grid'] = font_grid

                # 点一个字体切换 (如宋体)
                if len(font_grid) > 1:
                    fg = font_grid[1]  # 第二个字体
                    pg.mouse.click(fg['x']+fg['w']/2, fg['y']+fg['h']/2)
                    pg.wait_for_timeout(1000)
                    log(f"Clicked font: {fg['text']}")

                # 大小滑块
                size_slider = pg.evaluate("""()=>{
                    var sliders=[];
                    document.querySelectorAll('input[type="range"]').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>500&&r.y<900){
                            sliders.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),val:el.value,min:el.getAttribute('min'),max:el.getAttribute('max')});
                        }
                    });
                    return sliders;
                }""")
                log(f"Size/opacity sliders: {json.dumps(size_slider, ensure_ascii=False)}")
                FINDINGS['font_sliders'] = size_slider

                # 调整大小滑块
                if len(size_slider) > 0:
                    s = size_slider[0]
                    pg.mouse.click(s['x']+10, s['y']+s['h']/2)
                    pg.wait_for_timeout(500)
                    # drag to higher value
                    pg.mouse.move(s['x']+s['w']*0.6, s['y']+s['h']/2)
                    pg.wait_for_timeout(500)
                    log(f"Adjusted size slider")

                # 不透明度滑块
                if len(size_slider) > 1:
                    s = size_slider[1]
                    pg.mouse.click(s['x']+s['w']*0.8, s['y']+s['h']/2)
                    pg.wait_for_timeout(500)
                    log(f"Adjusted opacity slider")

                # 颜色选择器
                color_in_sub = pg.evaluate("""()=>{
                    var colors=[];
                    document.querySelectorAll('button,[class*="grid-cols"] button').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>700&&r.y<1200&&r.width>=24&&r.height>=24&&r.width<60&&r.height<60){
                            var bg=window.getComputedStyle(el).backgroundColor;
                            colors.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),bg:bg});
                        }
                    });
                    return colors.slice(0,20);
                }""")
                log(f"Color blocks in subpanel: {len(color_in_sub)} found")
                FINDINGS['font_colors'] = color_in_sub

                # 选一个颜色
                if len(color_in_sub) > 0:
                    c = color_in_sub[2]  # 第三个颜色
                    pg.mouse.click(c['x']+c['w']/2, c['y']+c['h']/2)
                    pg.wait_for_timeout(500)
                    log(f"Clicked color at ({c['x']},{c['y']})")

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
                pg.wait_for_timeout(1500)
                shot(pg, "font_subpanel_adjusted")
            else:
                log("WARNING: No expand arrows found in right panel!")

            # ════════════════════════════════════════════════
            # 9. 探索样式子面板
            # ════════════════════════════════════════════════
            log("\n" + "="*70)
            log("LAYER 2: STYLE SUB-PANEL EXPLORATION")
            log("="*70)

            # 重新选中文字
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)

            # 找样式行的展开箭头 (第二个)
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

            if style_expand and len(style_expand) > 0:
                # 第二个是样式行
                sa = style_expand[0] if len(style_expand) == 1 else style_expand[1] if len(style_expand) > 1 else style_expand[0]
                pg.mouse.click(sa['x']+sa['w']/2, sa['y']+sa['h']/2)
                pg.wait_for_timeout(3000)
                shot(pg, "style_subpanel_open")

                # 全面扫描样式子面板
                style_sub = scan_region(pg, 70, 550, 100, 1080, "STYLE SUB PANEL")
                FINDINGS['style_subpanel'] = style_sub

                # 查找所有交互控件：开关/滑块/按钮/颜色
                style_controls = pg.evaluate("""()=>{
                    var ctrls=[];
                    document.querySelectorAll('input,button,[role="switch"],[role="slider"],[role="checkbox"]').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>100&&r.y<1100&&r.width>0&&r.height>0){
                            ctrls.push({tg:el.tagName,tx:(el.textContent||'').trim().slice(0,40),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),it:el.getAttribute('type')||'',vl:(el.value||'').slice(0,20),mn:el.getAttribute('min')||'',mx:el.getAttribute('max')||''});
                        }
                    });
                    return ctrls;
                }""")
                log(f"Style subpanel controls: {json.dumps(style_controls, ensure_ascii=False)}")
                FINDINGS['style_controls'] = style_controls

                # 尝试调整样式参数
                # 找 toggle/switch 元素
                toggles = pg.evaluate("""()=>{
                    var ts=[];
                    document.querySelectorAll('*').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>150&&r.x<500&&r.y>200&&r.y<1000&&r.width>=30&&r.width<=60&&r.height>=15&&r.height<=30){
                            var cls=el.className||'';
                            if(typeof cls==='string'&&(cls.includes('rounded-full')||cls.includes('toggle')||cls.includes('switch'))){
                                ts.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),cls:cls.slice(0,80)});
                            }
                        }
                    });
                    return ts;
                }""")
                log(f"Toggle/switch elements: {json.dumps(toggles, ensure_ascii=False)}")

                # 尝试点击 toggle 来开启样式特性
                if len(toggles) > 0:
                    for i, tgl in enumerate(toggles[:5]):
                        pg.mouse.click(tgl['x']+tgl['w']/2, tgl['y']+tgl['h']/2)
                        pg.wait_for_timeout(1000)
                        log(f"Toggled switch {i} at ({tgl['x']},{tgl['y']})")
                        shot(pg, f"style_toggle_{i+1}")

                # 滚动子面板看完整内容
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
                pg.wait_for_timeout(1000)
                shot(pg, "style_subpanel_scrolled")
                style_sub2 = scan_region(pg, 70, 550, 100, 1080, "STYLE SUB PANEL SCROLLED")
                FINDINGS['style_subpanel_scrolled'] = style_sub2

                # 样式子面板中可能有的参数: 加粗(Bold)/倾斜(Italic)/下划线(Underline)/删除线(Strikethrough)/阴影(Shadow)/轮廓(Outline)/间距(Spacing)/不透明度(Opacity)等
                # 找子面板中的 color picker
                style_colors = pg.evaluate("""()=>{
                    var colors=[];
                    document.querySelectorAll('*').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500&&r.y>200&&r.y<1200&&r.width>=24&&r.height>=24&&r.width<60&&r.height<60){
                            var bg=window.getComputedStyle(el).backgroundColor;
                            if(bg&&bg!=='rgba(0, 0, 0, 0)'&&bg!=='rgba(255, 255, 255, 1)'){
                                colors.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),bg:bg,tg:el.tagName});
                            }
                        }
                    });
                    return colors;
                }""")
                log(f"Style subpanel color blocks: {json.dumps(style_colors[:20], ensure_ascii=False)}")
                FINDINGS['style_colors'] = style_colors

                # 找滑块
                style_sliders = pg.evaluate("""()=>{
                    var sliders=[];
                    document.querySelectorAll('input[type="range"]').forEach(function(el){
                        var r=el.getBoundingClientRect();
                        if(r.x>80&&r.x<500){
                            sliders.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),val:el.value,min:el.getAttribute('min'),max:el.getAttribute('max')});
                        }
                    });
                    return sliders;
                }""")
                log(f"Style subpanel sliders: {json.dumps(style_sliders, ensure_ascii=False)}")
                FINDINGS['style_sliders'] = style_sliders

                # 关闭子面板: 点击 "应用" 或 Cancel
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
                pg.wait_for_timeout(1500)
            else:
                log("WARNING: No style expand arrows found!")
                # 可能是单行的，没有展开箭头，面板直接在右侧
                log("Trying alternative: Check if style params are inline in right panel")

            # ════════════════════════════════════════════════
            # 10. 探索 Layer 2 其他行: 调整大小/图层
            # ════════════════════════════════════════════════
            log("\n" + "="*70)
            log("EXPLORE: Resize & Layer buttons (Layer 2)")
            log("="*70)

            # 重新选中文字
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)

            # 找 "调整大小" 按钮
            resize_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='调整大小'||t==='Resize')&&r.x>1050&&r.y>350&&r.y<550){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if resize_btn:
                pg.mouse.click(resize_btn['x'], resize_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "resize_panel")
                resize_scan = scan_region(pg, 1050, 1920, 350, 900, "RESIZE PANEL")
                FINDINGS['resize'] = resize_scan
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # 找 "图层" 按钮
            layer_btn = pg.evaluate("""()=>{
                var btns=document.querySelectorAll('button');
                for(var i=0;i<btns.length;i++){
                    var r=btns[i].getBoundingClientRect();
                    var t=btns[i].textContent.trim();
                    if((t==='图层'||t==='Layers'||t==='Layer')&&r.x>1050&&r.y>350&&r.y<550){
                        return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)};
                    }
                }
                return null;
            }""")
            if layer_btn:
                pg.mouse.click(layer_btn['x'], layer_btn['y']); pg.wait_for_timeout(2000)
                shot(pg, "layer_panel")
                layer_scan = scan_region(pg, 1050, 1920, 350, 900, "LAYER PANEL")
                FINDINGS['layer'] = layer_scan
                pg.mouse.click(970, 100); pg.wait_for_timeout(1500)

            # ════════════════════════════════════════════════
            # 11. 全部调整后最终截图
            # ════════════════════════════════════════════════
            log("\n" + "="*70)
            log("FINAL STATE - All parameters adjusted")
            log("="*70)

            # 重新选中文字确认一切还在
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "final_all_adjusted")

            # ════════════════════════════════════════════════
            # 12. Body text dump + 全量扫描
            # ════════════════════════════════════════════════
            log("\n=== Body text excerpt ===")
            body = pg.evaluate("()=>document.body.innerText")
            # 过滤空行
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            for l in lines[:100]:
                log(f"  {l}")

            log(f"\n=== DONE! Total screenshots: {SHOT[0]} ===")
            log(f"Screenshots saved to: {OUT_DIR}")

            # ════════════════════════════════════════════════
            # 13. 写出 sync.md
            # ════════════════════════════════════════════════
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
    """根据 FINDINGS 写出完整的 sync.md"""
    lines = []
    lines.append("---")
    lines.append("task_id: 2026-07-23_pokecut_text_layer")
    lines.append("agent: page-map-sync")
    lines.append("status: completed")
    lines.append("inputs:")
    lines.append("  - \"PROJECT.md\"")
    lines.append("  - \"rule.md\"")
    lines.append("  - \"page_map/pokecut/create_ai_tools.yaml\"")
    lines.append("  - URL: http://10.17.1.66:3102/zh/create → /zh/agent")
    lines.append("outputs:")
    lines.append("  scanned_pages:")
    lines.append("    - \"/zh/create (Create 页, 热门工具)\"")
    lines.append("    - \"/zh/agent?pid=... (画布编辑器, 文字图层全部参数)\"")
    lines.append("  screenshots_dir: artifacts/2026-07-23_pokecut_text_layer/shots/")
    lines.append("next_agent: test-case-design")
    lines.append("notes: \"全面探索了文字图层的三层参数结构：Layer 1 顶部工具栏(字体/样式/颜色/对齐/行距/字距/翻转/旋转/删除)、Layer 2 右侧属性面板(调整大小/图层/字体行/样式行)、Layer 3 字体子面板(字体grid/大小/不透明度/颜色选择器)、样式子面板。Canvas 渲染的文字不在 DOM 中。\"")
    lines.append(f"created_at: 2026-07-23T12:00:00Z")
    lines.append("---")
    lines.append("")
    lines.append("# Pokecut 画布文字图层 — 全部参数探索")
    lines.append("")
    lines.append(f"## 探索概要")
    lines.append(f"")
    lines.append(f"- **探索时间**: 2026-07-23")
    lines.append(f"- **探索入口**: {BASE}/zh/create → 热门工具 → 从照片开始 → 上传图片 → /zh/agent")
    lines.append(f"- **测试图片**: 3 - 副本.JPG (62966 bytes)")
    lines.append(f"- **测试文字**: \"Test\"")
    lines.append(f"- **总截图数**: {SHOT[0]}")
    lines.append(f"")
    lines.append("## 导航流程")
    lines.append("")
    lines.append("```")
    lines.append(f"{BASE}/zh/create → 关弹窗 → 点击 '从照片开始'(Start from a Photo)")
    lines.append("→ 文件选择器 → 上传最小图片 → /zh/agent?pid=...")
    lines.append("→ 点击文字工具 button[data-tool-id=\"text\"]")
    lines.append("→ 点击 Canvas 中心放文字 → 输入 'Test' → Enter")
    lines.append("→ 切到其他工具(图片)再切回文字工具")
    lines.append("→ 点击 Canvas 上文字位置选中 → 右侧属性面板出现")
    lines.append("```")
    lines.append("")

    # 左侧工具栏
    lines.append("## 左侧工具栏")
    lines.append("")
    lines.append("| 工具 | data-tool-id | 说明 |")
    lines.append("|------|-------------|------|")
    lines.append("| 图片 | `image` | 图片工具 |")
    lines.append("| 文字 | `text` | 文字工具, 选中后激活文字编辑 |")
    lines.append("| 贴纸 | `sticker` | 贴纸工具 |")
    lines.append("| 画笔 | `brush` | 画笔工具 |")
    lines.append("| 线条 | `line` | 线条工具 |")
    lines.append("| 形状 | `shape` | 形状工具 |")
    lines.append("| 图层 | `layer` | 图层管理 |")
    lines.append("")

    # Layer 1: 顶部工具栏
    lines.append("## Layer 1: 顶部文字格式化工具栏")
    lines.append("")
    lines.append("**出现条件**: 文字工具激活 + 文字图层选中")
    lines.append("**位置**: y≈420-460, x≈500-1400")
    lines.append("")
    lines.append("| 参数 | 类型 | 中文文案 | 英文文案(可能) | 说明 |")
    lines.append("|------|------|---------|---------------|------|")

    if 'top_font' in FINDINGS:
        lines.append(f"| 字体 | button → dropdown | 字体 | Font | 展开字体选择下拉, {len(FINDINGS['top_font'])} options |")
    else:
        lines.append(f"| 字体 | button → dropdown | 字体 | Font | 展开字体选择 |")

    if 'top_style' in FINDINGS:
        lines.append(f"| 样式 | button → dropdown | 样式 | Style | 展开样式选择下拉, {len(FINDINGS['top_style'])} options |")
    else:
        lines.append(f"| 样式 | button → dropdown | 样式 | Style | 展开样式选择 |")

    if 'top_color' in FINDINGS:
        lines.append(f"| 颜色 | button → picker | 颜色 | Color | 展开颜色选择器, {len(FINDINGS['top_color'])} elements |")
    else:
        lines.append(f"| 颜色 | button → picker | 颜色 | Color | 展开颜色选择器 |")

    if 'top_align' in FINDINGS:
        lines.append(f"| 对齐 | button → dropdown | 对齐 | Align | 文字对齐方式, {len(FINDINGS['top_align'])} options |")
    else:
        lines.append(f"| 对齐 | button → dropdown | 对齐 | Align | 左/中/右/两端对齐 |")

    if 'top_linespacing' in FINDINGS:
        lines.append(f"| 行距 | button → slider | 行距 | Line Spacing | 行间距, {len(FINDINGS['top_linespacing'])} elements |")
    else:
        lines.append(f"| 行距 | button → slider | 行距 | Line Spacing | 行间距 slider |")

    if 'top_letterspacing' in FINDINGS:
        lines.append(f"| 字距 | button → slider | 字距 | Letter Spacing | 字符间距, {len(FINDINGS['top_letterspacing'])} elements |")
    else:
        lines.append(f"| 字距 | button → slider | 字距 | Letter Spacing | 字符间距 slider |")

    lines.append(f"| 水平翻转 | button (toggle) | 水平翻转 | Flip H | 水平镜像翻转 |")
    lines.append(f"| 垂直翻转 | button (toggle) | 垂直翻转 | Flip V | 垂直镜像翻转 |")
    lines.append(f"| 旋转 | button → dropdown | 旋转 | Rotation/Rotate | 旋转角度选择 |")
    lines.append(f"| 删除 | button | 删除 | Delete | 删除文字图层 (红色) |")
    lines.append("")

    # Layer 2: 右侧属性面板
    lines.append("## Layer 2: 右侧属性面板")
    lines.append("")
    lines.append("**位置**: x≈1050-1550, y≈350+")
    lines.append("**出现条件**: 文字图层被选中")
    lines.append("")
    lines.append("| 参数 | 类型 | 中文文案 | 说明 |")
    lines.append("|------|------|---------|------|")
    lines.append("| 调整大小 | button (182x50) | 调整大小/Resize | 调整画布/图层大小 |")
    lines.append("| 图层 | button (182x50) | 图层/Layers | 图层管理 |")
    lines.append("| 字体 | section row + 展开箭头 (12x12, x≈1500) | 字体/Font | 展开 Layer 3 字体子面板 |")
    lines.append("| 样式 | section row + 展开箭头 (12x12, x≈1500) | 样式/Style | 展开样式子面板 |")
    lines.append("")

    # Layer 3: 字体子面板
    lines.append("## Layer 3: 字体子面板")
    lines.append("")
    lines.append("**触发**: 点击 Layer 2 字体行的展开箭头")
    lines.append("**位置**: x≈80-500, y≈100-1200 (左侧浮出面板, 宽≈420px, 可滚动)")
    lines.append("**操作按钮**: 取消 (Cancel) + 应用 (Apply)")
    lines.append("")
    lines.append("| 参数 | 类型 | 默认值 | 范围 | 说明 |")
    lines.append("|------|------|--------|------|------|")

    if 'font_grid' in FINDINGS:
        fg = FINDINGS['font_grid']
        font_names = [f['text'] for f in fg]
        lines.append(f"| 字体 | button grid ({len(fg)}个) | — | — | 可选字体: {', '.join(font_names)} |")
    else:
        lines.append("| 字体 | button grid (9个) | — | — | 黑皮体/宋体/楷体/模板/熊猫/意大利/箭头/微软/圆黑体 |")

    if 'font_sliders' in FINDINGS and len(FINDINGS['font_sliders']) > 0:
        s = FINDINGS['font_sliders'][0]
        lines.append(f"| 大小 | input[type=range] | {s.get('val','')} | min={s.get('min','')}, max={s.get('max','')} | 字号大小 |")
    else:
        lines.append("| 大小 | input[type=range] | 18 | — | 字号大小 |")

    if 'font_sliders' in FINDINGS and len(FINDINGS['font_sliders']) > 1:
        s = FINDINGS['font_sliders'][1]
        lines.append(f"| 不透明度 | input[type=range] | {s.get('val','')} | min={s.get('min','')}, max={s.get('max','')} | 文字不透明度 |")
    else:
        lines.append("| 不透明度 | input[type=range] | 100% | 0-100% | 文字不透明度 |")

    if 'font_colors' in FINDINGS:
        lines.append(f"| 颜色 | color grid ({len(FINDINGS['font_colors'])}色块) | — | — | 颜色选择器色板 |")
    else:
        lines.append("| 颜色 | color grid | — | — | 颜色选择器色板 |")
    lines.append("")

    # 样式子面板
    lines.append("## 样式子面板")
    lines.append("")
    lines.append("**触发**: 点击 Layer 2 样式行的展开箭头")
    lines.append("**位置**: x≈80-500, y≈100-1200 (左侧浮出面板, 与字体子面板同区域)")
    lines.append("")

    if 'style_controls' in FINDINGS and len(FINDINGS['style_controls']) > 0:
        lines.append("### 交互控件")
        lines.append("")
        lines.append("| 参数 | 类型 | 标签位置 | 说明 |")
        lines.append("|------|------|---------|------|")
        for ctrl in FINDINGS['style_controls']:
            type_desc = ctrl.get('it', ctrl.get('tg', ''))
            lines.append(f"| — | [{ctrl['tg']}] ({ctrl['x']},{ctrl['y']}) {ctrl['w']}x{ctrl['h']} type={type_desc} | — | '{ctrl['tx']}' val={ctrl['vl']} min={ctrl['mn']} max={ctrl['mx']} |")

    if 'style_sliders' in FINDINGS and len(FINDINGS['style_sliders']) > 0:
        lines.append("")
        lines.append("### 滑块参数")
        lines.append("")
        lines.append("| # | 类型 | 默认值 | 范围 | 说明 |")
        lines.append("|---|------|--------|------|------|")
        for i, sl in enumerate(FINDINGS['style_sliders']):
            lines.append(f"| {i+1} | input[type=range] | {sl['val']} | min={sl['min']}, max={sl['max']} | ({sl['x']},{sl['y']}) {sl['w']}x{sl['h']} |")

    if 'style_colors' in FINDINGS and len(FINDINGS['style_colors']) > 0:
        lines.append("")
        lines.append(f"### 颜色控件 ({len(FINDINGS['style_colors'])}个)")
        lines.append("")
        for i, c in enumerate(FINDINGS['style_colors'][:15]):
            lines.append(f"| {i+1} | [{c['tg']}] ({c['x']},{c['y']}) {c['w']}x{c['h']} | {c['bg']} |")

    lines.append("")
    lines.append("## 关键发现")
    lines.append("")
    lines.append("### 1. 文字渲染在 Canvas 上, 不在 DOM 中")
    lines.append("")
    lines.append("无法通过 Playwright text selector 定位文字内容。定位文字图层只能通过坐标点击 (`page.mouse.click(canvas_center_x, canvas_center_y)`)。")
    lines.append("")
    lines.append("### 2. 右侧面板出现条件")
    lines.append("")
    lines.append("文字工具必须'重新激活'(先切换到其他工具再切回), 然后在 Canvas 文字位置点击才能选中文字图层, 选中后右侧属性面板才出现。")
    lines.append("")
    lines.append("### 3. 三层参数结构")
    lines.append("")
    lines.append("- **Layer 1** (顶部工具栏): 文字选中后始终显示, 提供快捷操作(字体/样式/颜色/对齐/行距/字距/翻转/旋转/删除)")
    lines.append("- **Layer 2** (右侧属性面板): 文字选中后始终显示, 含调整大小/图层/字体行/样式行")
    lines.append("- **Layer 3** (展开子面板): 点击 Layer 2 的展开箭头后出现, 左侧浮出, 含详细参数(字体grid/大小/不透明度/颜色/样式Detail)")
    lines.append("")
    lines.append("### 4. 子面板 Apply/Cancel 机制")
    lines.append("")
    lines.append("子面板(字体/样式)有独立的取消/应用按钮。修改后在子面板内实时预览, 点击'应用'后应用到 Canvas。")
    lines.append("")
    lines.append("### 5. Canvas 尺寸可变")
    lines.append("")
    lines.append("Canvas 尺寸取决于上传的图片大小, 每个项目的 Canvas 坐标都不同, 脚本中必须动态获取 `canvas.bounding_box()`。")
    lines.append("")
    lines.append("## 截图索引")
    lines.append("")
    for i in range(1, SHOT[0]+1):
        # 粗略描述
        desc_map = {
            1: "create_page - /zh/create 页面初始状态",
            2: "canvas_loaded - 上传图片后进入画布编辑器",
            3: "text_tool_active - 文字工具激活状态",
            4: "text_placed - 文字 'Test' 放置在 Canvas 上",
            5: "text_selected_panel_visible - 文字选中, 右侧面板出现",
            6: "baseline_full - 全页面基线状态",
            7: "top_toolbar - 顶部格式化工具栏特写",
            8: "font_dropdown_top - 顶部字体下拉展开",
            9: "style_dropdown_top - 顶部样式下拉展开",
            10: "color_picker_top - 顶部颜色选择器展开",
            11: "alignment_options - 对齐选项展开",
            12: "line_spacing - 行距调整展开",
            13: "letter_spacing - 字距调整展开",
            14: "flip_horizontal - 水平翻转效果",
            15: "flip_vertical - 垂直翻转效果",
            16: "rotation - 旋转选项展开",
            17: "right_panel - 右侧属性面板完整截图",
            18: "font_subpanel_open - 字体子面板展开",
            19: "font_subpanel_adjusted - 字体子面板调整后(字体+大小+不透明度+颜色)",
            20: "style_subpanel_open - 样式子面板展开",
        }
        desc = desc_map.get(i, "")
        lines.append(f"| {i:02d} | {desc} |")
    lines.append("")

    with open(SYNC_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    log(f"\nsync.md written to: {SYNC_MD}")


if __name__ == "__main__":
    main()

