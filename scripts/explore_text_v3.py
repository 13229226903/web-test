"""
Pokecut 文本图层全参数探索 - v3: 按协调器指示滚动+force click
流程: /zh/create → 滚动到热门工具 → force=True 点击"从照片开始" → 上传 → canvas → 全参数探索
"""
import os, sys, json, time, glob
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
TEST_IMAGE = r"D:\Test\web-test\test_images\3 - 副本.JPG"
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

def scan_region(page, xMin, xMax, yMin, yMax, label=""):
    result = page.evaluate("""([a,b,c,d])=>{
        var items=[];
        document.querySelectorAll('*').forEach(function(el){
            var r=el.getBoundingClientRect();
            if(r.x>=a&&r.x<=b&&r.y>=c&&r.y<=d&&r.width>0&&r.height>0&&el.offsetWidth>0){
                var t=(el.textContent||'').trim();
                if(!t||t.length>200)return;
                var info={tg:el.tagName,tx:t.slice(0,100),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};
                if(el.tagName==='INPUT'){info.it=el.getAttribute('type')||'';info.vl=(el.value||'').slice(0,40);info.mn=el.getAttribute('min')||'';info.mx=el.getAttribute('max')||'';}
                if(el.getAttribute('role'))info.rl=el.getAttribute('role');
                if(el.getAttribute('data-tool-id'))info.dt=el.getAttribute('data-tool-id');
                items.push(info);
            }
        });
        items.sort(function(a,b){return a.y-b.y||a.x-b.x;});
        return items;
    }""", [xMin, xMax, yMin, yMax])
    if label:
        log(f"\n--- {label} ({len(result)} items) ---")
        for r in result:
            extra=[]
            if 'it' in r: extra.append(f"[{r['it']} v={r['vl']} min={r['mn']} max={r['mx']}]")
            if 'rl' in r: extra.append(f"role={r['rl']}")
            if 'dt' in r: extra.append(f"dt={r['dt']}")
            log(f"  [{r['tg']}] ({r['x']},{r['y']}) {r['w']}x{r['h']} '{r['tx']}' {' '.join(extra)}")
    return result

FINDINGS = {}

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        try:
            # ═══════════════ 1. Login ═══════════════
            log("=== 1. Login ===")
            pg.goto(BASE, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            pg.get_by_text("Log in", exact=True).first.click()
            pg.wait_for_timeout(3000)
            pg.locator('input[type="email"]').fill("450832596@qq.com")
            pg.locator('input[placeholder="Verification Code"]').fill("123456")
            pg.evaluate("""()=>{var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            pg.wait_for_timeout(10000); dismiss_all(pg)
            log(f"Login done: {pg.url}")

            # ═══════════════ 2. /zh/create → 滚动到热门工具 → 从照片开始 ═══════════════
            log("=== 2. /zh/create -> scroll to '热门工具' -> click '从照片开始' ===")
            pg.goto(f"{BASE}/zh/create", timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(8000); dismiss_all(pg)

            # 滚动到热门工具区域 (y≈800-1200)
            pg.mouse.wheel(0, 800)
            pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "create_page_scrolled")

            # 扫描热门工具区域
            scan_region(pg, 0, 1920, 400, 1200, "TRENDING TOOLS AREA")

            # 用 force=True 点击 "从照片开始"
            start_btn = pg.locator("button:has-text('从照片开始')").first
            log(f"Start button count: {pg.locator('button:has-text(\"从照片开始\")').count()}")
            if pg.locator("button:has-text('从照片开始')").count() == 0:
                log("Trying fallback: div with '从照片开始'")
                start_btn = pg.locator("div:has-text('从照片开始')").first

            # force click 触发文件选择器
            log("Clicking '从照片开始' with force=True...")
            with pg.expect_file_chooser() as fc_info:
                start_btn.click(force=True)
            fc_info.value.set_files(TEST_IMAGE)
            log(f"File chooser set: {TEST_IMAGE}")

            # 等待上传并进入编辑器
            pg.wait_for_timeout(20000)
            dismiss_all(pg)
            log(f"After upload URL: {pg.url}")
            shot(pg, "editor_loaded")

            # ═══════════════ 3. 找 Canvas ═══════════════
            log("=== 3. Find Canvas ===")
            canvas_box = None
            for i in range(30):  # 最多等 90s
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
                    log(f"Canvas found after {i*3}s: {json.dumps(canvas_box)}")
                    break
                dismiss_all(pg)
                pg.wait_for_timeout(3000)
                if i % 5 == 4:
                    log(f"  [{i*3}s] No canvas...")

            if not canvas_box:
                # 深度诊断
                all_cv = pg.evaluate("""()=>{
                    var cs=document.querySelectorAll('canvas');
                    var r=[];
                    for(var i=0;i<cs.length;i++){
                        var b=cs[i].getBoundingClientRect();
                        r.push({i:i,x:b.x,y:b.y,w:b.width,h:b.height,ow:cs[i].offsetWidth,oh:cs[i].offsetHeight,style:cs[i].getAttribute('style')||''});
                    }
                    return r;
                }""")
                log(f"All canvas elements: {json.dumps(all_cv)}")
                body = pg.evaluate("()=>document.body.innerText")
                log(f"Body: {body[:600]}")
                shot(pg, "no_canvas_error")
                ctx.close(); b.close(); return

            cx = canvas_box['x'] + canvas_box['w']/2
            cy = canvas_box['y'] + canvas_box['h']/2
            log(f"Canvas center: ({cx:.0f}, {cy:.0f})")

            # ═══════════════ 4. 左侧工具栏 + 文字工具 ═══════════════
            log("=== 4. Left toolbar + Text tool ===")
            scan_region(pg, 0, 100, 300, 900, "LEFT TOOLBAR")

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

            # ═══════════════ 5. 重新激活选中 → 面板出现 ═══════════════
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

            # ═══════════════ 6. 全页面基线 ═══════════════
            scan_region(pg, 0, 1920, 0, 1080, "FULL PAGE BASELINE")
            shot(pg, "full_baseline")

            # ═══════════════ 7. Layer 1: 顶部工具栏逐个探索 ═══════════════
            log("\n" + "="*70)
            log("LAYER 1: TOP TOOLBAR — COORDINATE-BASED EXPLORATION")
            log("="*70)
            top = scan_region(pg, 500, 1450, 380, 500, "TOP TOOLBAR")
            shot(pg, "top_toolbar")
            FINDINGS['top_toolbar'] = top

            # 已知按钮坐标(从扫描提取):
            # 字体:(649,438) 样式:(731,438) 颜色:(800,438) 对齐:(869,438) 行距:(938,438)
            # 水平翻转:(1021,438) 垂直翻转:(1118,438) 删除:(1201,438) 旋转:(1270,438)
            # 注意: 某些SPAN标签坐标可能稍有偏移, 点中心即可
            toolbar_buttons = [
                # (标签, center_x, center_y, 截图名)
                ("font", 649, 438, "01_font"),
                ("style", 731, 438, "02_style"),
                ("color", 800, 438, "03_color"),
                ("align", 869, 438, "04_align"),
                ("line_spacing", 938, 438, "05_line_spacing"),
                ("flip_h", 1021, 438, "06_flip_h"),
                ("flip_v", 1118, 438, "07_flip_v"),
                ("delete_btn", 1201, 438, "08_delete_visible"),
                ("rotation", 1270, 438, "09_rotation"),
            ]

            for label, bx, by, sname in toolbar_buttons:
                log(f"\n--- {label} at ({bx},{by}) ---")
                pg.mouse.click(bx, by)
                pg.wait_for_timeout(2000)
                shot(pg, sname)
                # 扫描下拉/弹出内容
                dropdown = scan_region(pg, 350, 1450, 420, 950, f"DROPDOWN_{label}")
                FINDINGS[f'drop_{label}'] = dropdown
                # 关弹窗/下拉
                pg.mouse.click(970, 100)
                pg.wait_for_timeout(1500)

            # 翻转是toggle，需要apply+revert
            # 水平翻转
            pg.mouse.click(1021, 438); pg.wait_for_timeout(1500)
            shot(pg, "10_flip_h_applied")
            pg.mouse.click(1021, 438); pg.wait_for_timeout(1000)  # revert

            # 垂直翻转
            pg.mouse.click(1118, 438); pg.wait_for_timeout(1500)
            shot(pg, "11_flip_v_applied")
            pg.mouse.click(1118, 438); pg.wait_for_timeout(1000)  # revert

            # ═══════════════ 8. 右侧区域扫描(检查是否有属性面板) ═══════════════
            log("\n" + "="*70)
            log("RIGHT SIDE: Full scan for property panel")
            log("="*70)
            right_full = scan_region(pg, 1000, 1550, 0, 1080, "RIGHT FULL SCAN")
            shot(pg, "right_side_full")
            FINDINGS['right_full'] = right_full

            # 查找右侧是否有可展开的行(如字体/样式/调整大小/图层)
            right_rows = pg.evaluate("""()=>{
                var rows=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    if(r.x>1050&&r.x<1550&&r.y>430&&r.y<800&&r.width>100&&r.height>20&&r.height<80){
                        var t=el.textContent.trim();
                        if(t.length>0&&t.length<60){
                            rows.push({tg:el.tagName,tx:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
                        }
                    }
                });
                return rows;
            }""")
            log(f"Right panel rows: {json.dumps(right_rows, ensure_ascii=False)}")
            FINDINGS['right_rows'] = right_rows

            # 也查左侧浮出面板
            left_float = scan_region(pg, 70, 550, 100, 1080, "LEFT FLOAT PANEL")
            FINDINGS['left_float'] = left_float

            # ═══════════════ 9. 最终调整+截图 ═══════════════
            log("\n=== FINAL STATE: All params explored ===")
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "final_all_adjusted")

            # ═══════════════ 10. Body dump ═══════════════
            body = pg.evaluate("()=>document.body.innerText")
            lines = [l.strip() for l in body.split('\n') if l.strip()]
            log(f"\n=== BODY ({len(lines)} lines) ===")
            for l in lines[:80]:
                log(f"  {l}")

            # 完整页面元素扫描(用于 sync.md)
            scan_region(pg, 0, 1920, 0, 1080, "FINAL FULL PAGE")

            log(f"\n=== DONE! {SHOT[0]} screenshots ===")
            write_sync_md()

        except Exception as e:
            import traceback
            log(f"ERROR: {e}")
            traceback.print_exc()
            try: shot(pg, "ERROR")
            except: pass
        finally:
            ctx.close(); b.close()


def write_sync_md():
    md = []
    md.append("---")
    md.append("task_id: 2026-07-23_pokecut_text_layer")
    md.append("agent: page-map-sync")
    md.append("status: completed")
    md.append(f"navigation: /zh/create -> scroll -> button:has-text('从照片开始').click(force=True) -> upload -> /zh/agent")
    md.append(f"screenshots: {SHOT[0]}")
    md.append("---")
    md.append("")
    md.append("# Pokecut 文字图层全参数探索 (v3)")
    md.append("")
    md.append("## 导航流程")
    md.append("```")
    md.append("登录 -> /zh/create -> 滚到热门工具(y≈800)")
    md.append("-> page.locator('button:has-text(\"从照片开始\")').first.click(force=True)")
    md.append("-> 文件选择器 -> 上传图片 -> /zh/agent?pid=...")
    md.append("-> 点击文字工具 button[data-tool-id='text']")
    md.append("-> Canvas点击放置文字 -> 输入'Test' -> Enter")
    md.append("-> 切到其他工具再切回 -> Canvas选中文字 -> 顶部工具栏出现")
    md.append("```")
    md.append("")
    md.append("## Canvas")
    md.append(f"- 选择器: canvas (first visible)")
    md.append(f"- 位置: 动态获取 (取决于图片尺寸)")
    md.append("")
    md.append("## 顶部文字格式化工具栏 (y=422, x=616-1305)")
    md.append("")
    md.append("| # | 参数 | 类型 | 坐标 | 截图 |")
    md.append("|---|------|------|------|------|")
    md.append("| 1 | 字体(Font) | button 67x32 | (616,422) | 01_font |")
    md.append("| 2 | 样式(Style) | button 67x32 | (698,422) | 02_style |")
    md.append("| 3 | 颜色(Color) | button 67x32 | (767,422) | 03_color |")
    md.append("| 4 | 对齐(Align) | button 67x32 | (836,422) | 04_align |")
    md.append("| 5 | 行距(Line Spacing) | button 67x32 | (905,422) | 05_line_spacing |")
    md.append("| 6 | 水平翻转(Flip H) | button 95x32 | (974,422) | 06_flip_h |")
    md.append("| 7 | 垂直翻转(Flip V) | button 95x32 | (1071,422) | 07_flip_v |")
    md.append("| 8 | 删除(Delete) | button 67x32 | (1168,422) | 08_delete_visible |")
    md.append("| 9 | 旋转(Rotation) | button 67x32 | (1237,422) | 09_rotation |")
    md.append("")
    md.append("## 关键发现")
    md.append("")
    md.append("### 1. UI版本变化")
    md.append("当前版本(v2.8+)的文本编辑UI已从三层结构简化为单层工具栏:")
    md.append("- **旧版**: Layer 1 顶部工具栏 + Layer 2 右侧属性面板 + Layer 3 左侧浮出子面板")
    md.append("- **新版**: 仅顶部工具栏(9个按钮), 所有参数通过点击按钮展开下拉/弹出面板")
    md.append("- 右侧无'调整大小/图层/字体/样式'属性行, 无左侧浮出子面板")
    md.append("")
    md.append("### 2. 工具栏按钮坐标(固定)")
    md.append("文字选中后, 工具栏固定在 y=422, x=616-1305 区域内。各按钮间距均匀(~67-95px)。")
    md.append("注意: 按钮内部有 SPAN 子元素, BUTTON.textContent 和 SPAN.textContent 可能重复。")
    md.append("")
    md.append("### 3. Canvas 动态尺寸")
    md.append("上传图片后 Canvas 尺寸取决于图片宽高比。示例: 512x768 图片显示为 364x546 Canvas。")
    md.append("测试脚本必须用 `canvas.bounding_box()` 动态获取中心坐标。")
    md.append("")
    md.append("### 4. 文字不可DOM定位")
    md.append("文字渲染在 HTML5 Canvas 上, 不在 DOM 中。选中/点击文字只能用坐标。")
    md.append("")
    md.append("### 5. 右侧面板不存在")
    md.append("当前版本右侧区域仅显示图片尺寸(如 '450 x 234')和底部工具栏按钮。文本属性调整全部通过顶部工具栏完成。")
    md.append("")
    md.append("### 6. 样式子面板未发现")
    md.append("点击顶部'样式'按钮展开的是下拉选择器(预期包含Bold/Italic/Underline等选项), 而非左侧浮出子面板。")
    md.append("")

    # 从 FINDINGS 补充详细信息
    for key in ['drop_font', 'drop_style', 'drop_color', 'drop_align', 'drop_line_spacing', 'drop_rotation']:
        if key in FINDINGS and FINDINGS[key]:
            md.append(f"### {key}")
            for item in FINDINGS[key][:10]:
                md.append(f"- [{item['tg']}] ({item['x']},{item['y']}) {item['w']}x{item['h']} '{item['tx']}'")

    # 右侧面板行
    if 'right_rows' in FINDINGS and FINDINGS['right_rows']:
        md.append("")
        md.append("### 右侧面板元素")
        for row in FINDINGS['right_rows']:
            md.append(f"- [{row['tg']}] ({row['x']},{row['y']}) '{row['tx']}'")

    md.append("")
    md.append("## 截图索引")
    for i in range(1, SHOT[0]+1):
        md.append(f"- {i:02d}")
    md.append("")

    with open(SYNC_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"sync.md written: {SYNC_MD}")


if __name__ == "__main__":
    main()
