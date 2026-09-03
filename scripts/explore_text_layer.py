"""
探索 Pokecut 画布文字图层全部参数 — v11: 精确草稿tab选择器 + 完整面板探索。
"""
import os, sys, json, time, glob, re
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts", "2026-07-23_pokecut_text_layer", "shots")
os.makedirs(OUT_DIR, exist_ok=True)

for f in glob.glob(os.path.join(OUT_DIR, "*.png")):
    try: os.remove(f)
    except: pass

SHOT = [0]
def shot(page, name):
    SHOT[0] += 1
    fpath = os.path.join(OUT_DIR, f"{SHOT[0]:02d}_{name}.png")
    page.screenshot(path=fpath, full_page=False)
    print(f"  [SHOT {SHOT[0]:02d}] {name}")
    return fpath

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def dismiss_all(page):
    try:
        page.evaluate("""()=>{
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o){
                var bg=window.getComputedStyle(o).backgroundColor;
                if(bg&&bg.includes('rgba')&&(bg.includes('0.3')||bg.includes('0.5')))o.remove();
            });
        }""")
        page.wait_for_timeout(1000)
    except: pass

def dump_region(page, label, xMin, xMax, yMin, yMax):
    """Dump all interactive and text elements in a region."""
    result = page.evaluate("""([xMin,xMax,yMin,yMax])=>{
        var items=[];
        document.querySelectorAll('*').forEach(function(el){
            var r=el.getBoundingClientRect();
            if(r.x>=xMin&&r.x<=xMax&&r.y>=yMin&&r.y<=yMax&&r.width>0&&r.height>0&&el.offsetWidth>0){
                var t=el.textContent.trim();
                if(!t||t.length>200)return;
                var info={tg:el.tagName,tx:t.slice(0,120),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),ch:el.children.length};
                if(el.tagName==='INPUT'){info.it=el.getAttribute('type')||'';info.vl=(el.value||'').slice(0,40);info.mn=el.getAttribute('min')||'';info.mx=el.getAttribute('max')||'';}
                if(el.getAttribute('role'))info.rl=el.getAttribute('role');
                if(el.getAttribute('data-tool-id'))info.dt=el.getAttribute('data-tool-id');
                if(el.getAttribute('aria-label'))info.al=el.getAttribute('aria-label');
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
        if 'al' in r: extra.append(f"aria={r['al']}")
        log(f"  [{r['tg']}] ({r['x']},{r['y']}) {r['w']}x{r['h']} ch={r['ch']} '{r['tx']}' {' '.join(extra)}")
    return result

def scroll_region(page, xMin, xMax):
    return page.evaluate("""([xMin,xMax])=>{
        var all=document.querySelectorAll('*');
        for(var i=0;i<all.length;i++){
            var r=all[i].getBoundingClientRect();
            if(r.x>=xMin&&r.x<=xMax&&r.width>200&&r.height>200&&all[i].scrollHeight>all[i].clientHeight+10){
                all[i].scrollTop=all[i].scrollHeight;
                return 'scrolled sh='+all[i].scrollHeight+' ch='+all[i].clientHeight;
            }
        }
        return 'no_scroll';
    }""", [xMin, xMax])

def click_center(page, el_info):
    """Click center of an element using position info."""
    pg = page
    pg.mouse.click(el_info['x']+el_info['w']/2, el_info['y']+el_info['h']/2)

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        try:
            # ═══════════════ 1. 登录 ═══════════════
            log("=== 1. Login ===")
            pg.goto(BASE, timeout=120000); pg.wait_for_timeout(5000)
            pg.get_by_text("Log in", exact=True).first.click(); pg.wait_for_timeout(3000)
            pg.locator('input[type="email"]').fill("450832596@qq.com")
            pg.locator('input[placeholder="Verification Code"]').fill("123456")
            pg.evaluate("""()=>{var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            pg.wait_for_timeout(10000); dismiss_all(pg)
            log(f"Login done: {pg.url}")

            # ═══════════════ 2. 项目页 → 草稿 tab → 第一个项目 ═══════════════
            log("=== 2. Project page -> Drafts tab -> first project ===")
            pg.goto(f"{BASE}/zh/project", timeout=60000); pg.wait_for_timeout(8000)
            dismiss_all(pg)
            shot(pg, "project_page")

            # 精确选择器(来自 coordinator): span.text-pc-normal-btn:has-text("草稿")
            drafts_sel = 'span.text-pc-normal-btn:has-text("草稿")'
            drafts_count = pg.locator(drafts_sel).count()
            log(f"Drafts tab count with selector '{drafts_sel}': {drafts_count}")

            if drafts_count > 0:
                box = pg.locator(drafts_sel).first.bounding_box()
                log(f"Drafts tab at ({box['x']:.0f},{box['y']:.0f}) {box['width']:.0f}x{box['height']:.0f}")
                pg.locator(drafts_sel).first.click()
                pg.wait_for_timeout(3000)
                log("Clicked drafts tab")
            else:
                log("WARNING: drafts tab not found, trying fallback...")
                # Fallback: find any element with text "草稿" above y=200 (tab bar)
                fallback = pg.evaluate("""()=>{
                    var all=document.querySelectorAll('*');
                    for(var i=0;i<all.length;i++){
                        var t=all[i].textContent.trim();
                        var r=all[i].getBoundingClientRect();
                        if(t==='草稿'&&r.y<200&&r.width>10){
                            return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};
                        }
                    }
                    return null;
                }""")
                if fallback:
                    pg.mouse.click(fallback['x'], fallback['y'])
                    pg.wait_for_timeout(3000)
                    log(f"Fallback click at ({fallback['x']},{fallback['y']})")
                else:
                    log("ERROR: Cannot find drafts tab!")

            dismiss_all(pg)
            shot(pg, "project_drafts")

            # 找第一个项目卡片并点击
            project_cards = pg.evaluate("""()=>{
                var cards=[];
                document.querySelectorAll('a,[class*="cursor-pointer"]').forEach(function(el){
                    var b=el.getBoundingClientRect();
                    if(b.width>=100&&b.height>=100&&b.y>=200){
                        cards.push({x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),tg:el.tagName,href:(el.getAttribute("href")||"").substring(0,100)});
                    }
                });
                return cards.slice(0,10);
            }""")
            log(f"Project cards: {json.dumps(project_cards, ensure_ascii=False)}")

            if project_cards:
                card = project_cards[0]
                pg.mouse.click(card['x']+card['w']/2, card['y']+card['h']/2)
            else:
                log("ERROR: No project cards found!")
                ctx.close(); b.close(); return

            pg.wait_for_timeout(10000); dismiss_all(pg)
            log(f"Canvas editor URL: {pg.url}")
            shot(pg, "canvas_editor")

            # ═══════════════ 3. 激活文字工具 + 添加文字 ═══════════════
            log("=== 3. Add text ===")

            # 左侧工具按钮
            left_tools = pg.evaluate("""()=>{
                var tools=[];
                document.querySelectorAll('[data-tool-id],button').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    if(r.x<100&&r.y>400&&r.width>20&&r.height>20){
                        tools.push({dt:el.getAttribute('data-tool-id')||'',tx:(el.textContent||'').trim().slice(0,30),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
                    }
                });
                return tools;
            }""")
            log(f"Left sidebar tools: {json.dumps(left_tools, ensure_ascii=False)}")

            # 找文字/图片工具
            text_t = next((t for t in left_tools if t['dt']=='text'), None)
            img_t = next((t for t in left_tools if t['dt']=='image'), None)

            if not text_t:
                log("ERROR: text tool not found!")
                ctx.close(); b.close(); return

            # 点击文字工具
            click_center(pg, text_t); pg.wait_for_timeout(2000)
            shot(pg, "text_tool_active")

            # 点击 canvas 并输入文字
            canvas_box = pg.locator('canvas').first.bounding_box()
            cx = canvas_box['x']+canvas_box['width']/2
            cy = canvas_box['y']+canvas_box['height']/2
            log(f"Canvas center: ({cx:.0f},{cy:.0f})")

            pg.mouse.click(cx, cy); pg.wait_for_timeout(1500)
            pg.keyboard.type("TestText"); pg.wait_for_timeout(1000)
            shot(pg, "text_typed")
            pg.keyboard.press("Enter"); pg.wait_for_timeout(1500)
            shot(pg, "text_submitted")

            # ═══════════════ 4. 重新激活文字工具 + 选中文字图层 ═══════════════
            log("=== 4. Re-select text layer ===")
            if img_t:
                click_center(pg, img_t); pg.wait_for_timeout(1000)
                log("  Switched to image tool")
            click_center(pg, text_t); pg.wait_for_timeout(3000)
            log("  Switched back to text tool")
            # 点击 canvas 上的文字来选中 (坐标同添加文字位置)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            shot(pg, "text_layer_selected")

            # ═══════════════ 5. 扫描顶部工具栏 ═══════════════
            log("=== 5. Top toolbar scan ===")
            top_tb = dump_region(pg, "TOP TOOLBAR", 500, 1500, 300, 400)
            shot(pg, "top_toolbar")

            # ═══════════════ 6. 扫描右侧面板 ═══════════════
            log("=== 6. Right panel scan ===")
            # 先宽范围扫描
            right1 = dump_region(pg, "RIGHT PANEL (wide)", 1000, 1920, 350, 950)
            right2 = dump_region(pg, "RIGHT PANEL (floating)", 80, 550, 100, 1080)
            shot(pg, "panels_scan")

            # 找左侧浮出面板中的展开箭头
            floating_btns = pg.evaluate("""()=>{
                var items=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    var t=el.textContent.trim();
                    if(r.x>100&&r.x<550&&r.y>120&&r.y<1000&&r.width>30&&el.children.length===0&&t.length>0&&t.length<30){
                        items.push({tg:el.tagName,tx:t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
                    }
                });
                return items;
            }""")
            log(f"Floating panel clickable items: {json.dumps(floating_btns, ensure_ascii=False)}")

            # 找右侧面板内的所有 section 行 (font/style/etc)
            right_rows = pg.evaluate("""()=>{
                var rows=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    var t=el.textContent.trim();
                    if(r.x>1100&&r.x<1550&&r.y>430&&r.y<800&&r.width>100&&r.height>40&&r.height<80&&el.children.length>0){
                        rows.push({tg:el.tagName,tx:t.slice(0,80),x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
                    }
                });
                return rows;
            }""")
            log(f"Right panel section rows: {json.dumps(right_rows, ensure_ascii=False)}")

            # ═══════════════ 7. 字体子面板探索 ═══════════════
            log("=== 7. Font sub-panel ===")
            # 找字体 section 的展开箭头 (通常在 x=1500 附近, 12x12)
            font_arrow = pg.evaluate("""()=>{
                var items=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    if(r.x>1480&&r.x<1540&&r.y>480&&r.y<620&&r.width>=8&&r.width<=20&&r.height>=8&&r.height<=20){
                        var p=el.parentElement;
                        items.push({tg:el.tagName,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),parent:(p?p.textContent.trim().slice(0,40):'')});
                    }
                });
                return items;
            }""")
            log(f"Font expand arrows: {json.dumps(font_arrow, ensure_ascii=False)}")

            if font_arrow:
                fa = font_arrow[0]
                pg.mouse.click(fa['x']+fa['w']/2, fa['y']+fa['h']/2)
                pg.wait_for_timeout(2500)
                shot(pg, "font_panel_open")

                # 扫描浮出字体面板
                font_data = dump_region(pg, "FONT FLOATING PANEL", 80, 550, 100, 1080)
                scroll_region(pg, 80, 550); pg.wait_for_timeout(1000)
                shot(pg, "font_panel_scrolled")
                font_data2 = dump_region(pg, "FONT PANEL SCROLLED", 80, 550, 100, 1080)

                # 关闭: 找 Cancel/取消
                pg.evaluate("""()=>{
                    var btns=document.querySelectorAll('button');
                    for(var i=0;i<btns.length;i++){
                        var t=btns[i].textContent.trim();var r=btns[i].getBoundingClientRect();
                        if((t==='取消'||t==='Cancel')&&r.x>800&&r.y<140){
                            btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                            return;
                        }
                    }
                }""")
                pg.wait_for_timeout(1500)
            else:
                log("WARNING: No font expand arrow found!")

            # ═══════════════ 8. 样式子面板探索 ═══════════════
            log("=== 8. Style sub-panel ===")
            # 重新选中文字
            if img_t:
                click_center(pg, img_t); pg.wait_for_timeout(1000)
            click_center(pg, text_t); pg.wait_for_timeout(3000)
            pg.mouse.click(cx, cy); pg.wait_for_timeout(2000)
            dismiss_all(pg)
            shot(pg, "text_reselected_for_style")

            # 找样式 section 的展开箭头
            style_arrow = pg.evaluate("""()=>{
                var items=[];
                document.querySelectorAll('*').forEach(function(el){
                    var r=el.getBoundingClientRect();
                    if(r.x>1480&&r.x<1540&&r.y>560&&r.y<750&&r.width>=8&&r.width<=20&&r.height>=8&&r.height<=20){
                        var p=el.parentElement;
                        items.push({tg:el.tagName,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),parent:(p?p.textContent.trim().slice(0,40):'')});
                    }
                });
                return items;
            }""")
            log(f"Style expand arrows: {json.dumps(style_arrow, ensure_ascii=False)}")

            if style_arrow:
                sa = style_arrow[0]
                pg.mouse.click(sa['x']+sa['w']/2, sa['y']+sa['h']/2)
                pg.wait_for_timeout(2500)
                shot(pg, "style_panel_open")

                style_data = dump_region(pg, "STYLE FLOATING PANEL", 80, 550, 100, 1080)
                scroll_region(pg, 80, 550); pg.wait_for_timeout(1000)
                shot(pg, "style_panel_scrolled")
                style_data2 = dump_region(pg, "STYLE PANEL SCROLLED", 80, 550, 100, 1080)

                # Close
                pg.evaluate("""()=>{
                    var btns=document.querySelectorAll('button');
                    for(var i=0;i<btns.length;i++){
                        var t=btns[i].textContent.trim();var r=btns[i].getBoundingClientRect();
                        if((t==='取消'||t==='Cancel')&&r.x>800&&r.y<140){
                            btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                            return;
                        }
                    }
                }""")
                pg.wait_for_timeout(1500)
            else:
                log("WARNING: No style expand arrow found!")
                # 扩大扫描范围看右侧面板所有可点击元素
                right_full = dump_region(pg, "RIGHT PANEL ALL", 1000, 1920, 0, 1080)
                shot(pg, "right_panel_full_detail")

            # ═══════════════ 9. 最终状态 ═══════════════
            log("=== 9. Final state ===")
            shot(pg, "final_state")

            # Body text dump
            body = pg.evaluate("()=>document.body.innerText")
            log(f"\n=== BODY TEXT ({len(body)} chars) ===")
            log(body[:8000])

            log(f"\n=== DONE! Total screenshots: {SHOT[0]} ===")

        except Exception as e:
            import traceback
            log(f"ERROR: {e}")
            traceback.print_exc()
            try: shot(pg, "ERROR")
            except: pass
        finally:
            ctx.close()
            b.close()

if __name__ == "__main__":
    main()
