"""探索 Pokecut 画布文字图层的样式子面板和未探索的右侧面板参数。

探索内容:
1. 右侧面板"样式"行展开 → 子面板内容 (加粗/倾斜/下划线/描边/阴影/轮廓等)
2. 右侧面板是否有其他未探索的行 (如间距等)
3. 每个参数的名称、类型、selector、取值
"""
import os, sys, json, time
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts", "2026-07-23_pokecut_text_layer", "shots")
os.makedirs(OUT_DIR, exist_ok=True)

SHOT_ID = [0]
def shot(page, name):
    SHOT_ID[0] += 1
    page.screenshot(path=os.path.join(OUT_DIR, f"{SHOT_ID[0]:02d}_{name}.png"), full_page=False)
    print(f"  [截图] {SHOT_ID[0]:02d}_{name}")

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def dismiss_overlay(page):
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5")))
                o.remove();
        });
    }""")
    page.wait_for_timeout(1000)

def scan_region(page, x_min, x_max, y_min, y_max, label="区域"):
    """扫描指定矩形区域内的所有可见元素"""
    result = page.evaluate("""([x_min, x_max, y_min, y_max]) => {
        var results = [];
        var all = document.querySelectorAll('*');
        all.forEach(function(el) {
            var r = el.getBoundingClientRect();
            if (r.x >= x_min && r.x <= x_max && r.y >= y_min && r.y <= y_max &&
                r.width > 0 && r.height > 0 && el.offsetWidth > 0) {
                var t = (el.textContent || '').trim();
                if (t.length > 300) return;
                var info = {
                    tg: el.tagName, tx: t.slice(0, 120),
                    x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height),
                    ch: el.children.length
                };
                if (el.tagName === 'INPUT') {
                    info.it = el.getAttribute('type') || '';
                    info.vl = (el.value || '').slice(0, 40);
                    info.mn = el.getAttribute('min') || '';
                    info.mx = el.getAttribute('max') || '';
                    info.step = el.getAttribute('step') || '';
                }
                if (el.getAttribute('role')) info.rl = el.getAttribute('role');
                if (el.getAttribute('data-tool-id')) info.dt = el.getAttribute('data-tool-id');
                // 检查是否为 clickable
                var cs = window.getComputedStyle(el);
                if (cs.cursor === 'pointer') info.cursor = 'pointer';
                results.push(info);
            }
        });
        results.sort(function(a,b){return a.y-b.y||a.x-b.x;});
        return results;
    }""", [x_min, x_max, y_min, y_max])
    log(f"\n--- {label} ({len(result)} 个元素) ---")
    for e in result:
        extra = []
        if 'it' in e: extra.append(f"[{e['it']} val='{e['vl']}' min={e['mn']} max={e['mx']} step={e['step']}]")
        if 'rl' in e: extra.append(f"role={e['rl']}")
        if 'cursor' in e: extra.append(f"clickable")
        log(f"  [{e['tg']}] ({e['x']},{e['y']}) {e['w']}x{e['h']} ch={e['ch']} '{e['tx']}' {' '.join(extra)}")

def scan_all_buttons(page):
    """扫描全页面所有 button/input/select 等交互元素"""
    result = page.evaluate("""() => {
        var r = [];
        var all = document.querySelectorAll('input, button, select, textarea, [role="slider"], [role="combobox"], [role="button"], [role="switch"], [role="checkbox"]');
        all.forEach(function(el) {
            var b = el.getBoundingClientRect();
            if (b.width > 0 && b.height > 0) {
                r.push({
                    tg: el.tagName, tx: (el.textContent||'').trim().slice(0, 60),
                    x: Math.round(b.x), y: Math.round(b.y),
                    w: Math.round(b.width), h: Math.round(b.height),
                    it: el.getAttribute('type') || '', vl: (el.value||'').slice(0, 40),
                    mn: el.getAttribute('min')||'', mx: el.getAttribute('max')||'',
                    step: el.getAttribute('step')||'',
                    rl: el.getAttribute('role')||'',
                    cls: (el.className||'').slice(0, 200)
                });
            }
        });
        r.sort(function(a,b){return a.y-b.y||a.x-b.x;});
        return r;
    }""")
    log(f"\n========== 全页面交互元素 ({len(result)}) ==========")
    for e in result:
        log(f"  [{e['tg']}] ({e['x']},{e['y']}) {e['w']}x{e['h']} '{e['tx']}' type={e['it']} val={e['vl']} min={e['mn']} max={e['mx']} step={e['step']} role={e['rl']}")
    return result

def scan_all_text_content(page):
    """扫描全页面所有含文本内容的元素"""
    result = page.evaluate("""() => {
        var r = [];
        var all = document.querySelectorAll('*');
        var seen = new Set();
        all.forEach(function(el) {
            if (el.children.length > 0) return; // 只取叶子节点
            var t = el.textContent.trim();
            if (!t || t.length > 200) return;
            var b = el.getBoundingClientRect();
            if (b.width > 0 && b.height > 0 && b.x >= 0 && b.y >= 0) {
                var key = t + '|' + Math.round(b.x) + '|' + Math.round(b.y);
                if (seen.has(key)) return;
                seen.add(key);
                r.push({
                    tg: el.tagName, tx: t.slice(0, 100),
                    x: Math.round(b.x), y: Math.round(b.y),
                    w: Math.round(b.width), h: Math.round(b.height)
                });
            }
        });
        r.sort(function(a,b){return a.y-b.y||a.x-b.x;});
        return r;
    }""")
    return result

def enter_canvas(pg):
    """进入第一个项目的画布页面"""
    pg.goto(f"{BASE}/zh/project", timeout=60000); pg.wait_for_timeout(8000); dismiss_overlay(pg)

    # 尝试多个缩略图位置
    positions = [
        (330, 344),   # 第一个缩略图中心
        (457+109, 235+109),  # 第二个
        (330, 550),   # 第二行第一个
    ]
    for px, py in positions:
        pg.mouse.click(px, py); pg.wait_for_timeout(5000); dismiss_overlay(pg)
        if "agent" in pg.url:
            log(f"进入画布成功: click ({px},{py}) -> {pg.url}")
            return True
        log(f"({px},{py}) 未导航, URL={pg.url}")

    # JS fallback
    pg.evaluate("""() => {
        var cards = document.querySelectorAll('[class*="cursor-pointer"]');
        for (var i=0; i<cards.length; i++) {
            var r = cards[i].getBoundingClientRect();
            if (r.width > 150 && r.height > 150 && r.y > 200) {
                cards[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return;
            }
        }
    }""")
    pg.wait_for_timeout(8000); dismiss_overlay(pg)
    log(f"JS fallback后 URL: {pg.url}")
    return "agent" in pg.url


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False)  # headful 便于调试
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # ═══ 登录 ═══
        log("登录...")
        pg.goto(BASE, timeout=120000); pg.wait_for_timeout(5000)
        pg.get_by_text("Log in", exact=True).first.click(); pg.wait_for_timeout(3000)
        pg.locator('input[type="email"]').fill("450832596@qq.com")
        pg.locator('input[placeholder="Verification Code"]').fill("123456")
        pg.evaluate("""()=>{var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
        pg.wait_for_timeout(10000); dismiss_overlay(pg)
        log(f"登录完成: {pg.url}")

        # ═══ 进入画布 ═══
        if not enter_canvas(pg):
            log("错误: 无法进入画布!"); shot(pg, "error_no_canvas")
            ctx.close(); b.close(); return

        pg.wait_for_timeout(5000); dismiss_overlay(pg)
        shot(pg, "10_canvas_initial")

        # ═══ 文字工具 + 添加文字 ═══
        tb = pg.locator('[data-tool-id="text"]').first.bounding_box()
        if not tb:
            log("错误: 找不到文字工具按钮!")
            ctx.close(); b.close(); return
        pg.mouse.click(tb["x"]+tb["width"]/2, tb["y"]+tb["height"]/2)
        pg.wait_for_timeout(2000)
        log("文字工具已激活")

        # Canvas 上创建文字
        canvas = pg.locator('canvas').first
        cb = canvas.bounding_box()
        if not cb:
            log("错误: 找不到 Canvas!")
            ctx.close(); b.close(); return
        log(f"Canvas: ({cb['x']:.0f},{cb['y']:.0f}) {cb['width']:.0f}x{cb['height']:.0f}")

        ccx = cb['x'] + cb['width']/2; ccy = cb['y'] + cb['height']/2
        pg.mouse.click(ccx, ccy); pg.wait_for_timeout(1500)
        pg.keyboard.type("TestStyle"); pg.wait_for_timeout(1000)
        pg.keyboard.press("Enter"); pg.wait_for_timeout(1500)

        # ═══ 重新激活文字工具 (选中文字 → 面板出现) ═══
        ib = pg.locator('[data-tool-id="image"]').first.bounding_box()
        pg.mouse.click(ib["x"]+ib["width"]/2, ib["y"]+ib["height"]/2)
        pg.wait_for_timeout(1000)
        pg.mouse.click(tb["x"]+tb["width"]/2, tb["y"]+tb["height"]/2)
        pg.wait_for_timeout(3000)
        shot(pg, "11_text_selected")

        # ═══ 第一步: 扫描右侧面板所有可点击的行 ═══
        log("\n" + "="*60)
        log("第一步: 扫描右侧面板区域 (x=1100-1550, y=400-800)")
        scan_region(pg, 1100, 1550, 400, 800, "右侧面板")

        # 扫描整个右侧面板区域，找所有带文本的元素
        right_panel_items = page_text_in_area(pg, 1100, 1550, 400, 1080)
        log(f"\n右侧面板文本内容:")
        for item in right_panel_items:
            log(f"  [{item['tg']}] ({item['x']},{item['y']}) '{item['tx']}'")

        # ═══ 第二步: 点击"样式"行展开箭头 ═══
        # 根据之前探索, 样式行展开箭头在 x=1500, y=698
        log("\n" + "="*60)
        log("第二步: 点击样式行展开箭头")

        # 先精确查找样式行的展开箭头
        expand_arrows = pg.evaluate("""() => {
            var results = [];
            var all = document.querySelectorAll('*');
            all.forEach(function(el) {
                var r = el.getBoundingClientRect();
                if (r.x > 1100 && r.x < 1550 && r.y > 600 && r.y < 750 &&
                    r.width > 0 && r.width < 30 && r.height > 0 && r.height < 30) {
                    var cs = window.getComputedStyle(el);
                    results.push({
                        x: Math.round(r.x), y: Math.round(r.y),
                        w: Math.round(r.width), h: Math.round(r.height),
                        tg: el.tagName, cursor: cs.cursor,
                        cls: (el.className||'').slice(0, 100)
                    });
                }
            });
            return results;
        }""")

        style_arrow = None
        for a in expand_arrows:
            log(f"  小图标: ({a['x']},{a['y']}) {a['w']}x{a['h']} {a['tg']} cursor={a['cursor']}")

        # 根据已知位置 (1500, 698) 点击样式展开箭头
        log("点击样式展开箭头 (1500, 698)...")
        pg.mouse.click(1500, 698)
        pg.wait_for_timeout(3000)
        shot(pg, "12_style_subpanel_open")

        # ═══ 第三步: 扫描样式子面板 ═══
        log("\n" + "="*60)
        log("第三步: 扫描样式子面板 (x=80-550, y=100-1080)")

        # 扫描完整子面板区域
        style_panel = scan_region(pg, 80, 550, 100, 1080, "样式子面板完整区域")

        # 同时扫描更广区域，确保不遗漏
        scan_region(pg, 80, 550, 1080, 1200, "样式子面板下方(超出视口)")

        # 在子面板中查找所有交互控件
        subpanel_interactives = pg.evaluate("""() => {
            var r = [];
            var all = document.querySelectorAll('input, button, select, [role="slider"], [role="switch"], [role="checkbox"], [role="combobox"]');
            all.forEach(function(el) {
                var b = el.getBoundingClientRect();
                if (b.width > 0 && b.height > 0 && b.x > 80 && b.x < 550 && b.y > 100 && b.y < 1200) {
                    var info = {
                        tg: el.tagName, tx: (el.textContent||'').trim().slice(0, 80),
                        x: Math.round(b.x), y: Math.round(b.y),
                        w: Math.round(b.width), h: Math.round(b.height),
                        it: el.getAttribute('type') || '', vl: (el.value||'').slice(0, 40),
                        mn: el.getAttribute('min')||'', mx: el.getAttribute('max')||'',
                        step: el.getAttribute('step')||'',
                        rl: el.getAttribute('role')||'',
                        ph: el.getAttribute('placeholder')||'',
                        cls: (el.className||'').slice(0, 150)
                    };
                    r.push(info);
                }
            });
            r.sort(function(a,b){return a.y-b.y||a.x-b.x;});
            return r;
        }""")
        log(f"\n样式子面板交互元素 ({len(subpanel_interactives)}):")
        for e in subpanel_interactives:
            log(f"  [{e['tg']}] ({e['x']},{e['y']}) {e['w']}x{e['h']} '{e['tx']}' type={e['it']} val={e['vl']} min={e['mn']} max={e['mx']} step={e['step']} role={e['rl']} placeholder={e['ph']}")

        # ═══ 第四步: 查找输入控件（滑块/输入框）的详细参数 ═══
        log("\n" + "="*60)
        log("第四步: 输入控件详情")

        inputs_detail = pg.evaluate("""() => {
            var r = [];
            var all = document.querySelectorAll('input, [role="slider"]');
            all.forEach(function(el) {
                var b = el.getBoundingClientRect();
                if (b.width > 0 && b.height > 0 && b.x > 80 && b.x < 550) {
                    var attrs = {};
                    for (var i=0; i<el.attributes.length; i++) {
                        attrs[el.attributes[i].name] = el.attributes[i].value;
                    }
                    r.push({
                        x: Math.round(b.x), y: Math.round(b.y),
                        w: Math.round(b.width), h: Math.round(b.height),
                        tg: el.tagName,
                        attrs: attrs,
                        val: el.value,
                        bg: window.getComputedStyle(el).backgroundColor
                    });
                }
            });
            return r;
        }""")
        for inp in inputs_detail:
            log(f"  [{inp['tg']}] ({inp['x']},{inp['y']}) {inp['w']}x{inp['h']} val={inp['val']} attrs={json.dumps(inp['attrs'], ensure_ascii=False)[:300]}")

        # ═══ 第五步: 滚动子面板查看所有内容 ═══
        log("\n" + "="*60)
        log("第五步: 滚动子面板")

        scroll_info = pg.evaluate("""() => {
            var all = document.querySelectorAll('*');
            var found = [];
            for (var i=0; i<all.length; i++) {
                var r = all[i].getBoundingClientRect();
                if (r.x > 80 && r.x < 550 && r.width > 200 && r.height > 200 &&
                    all[i].scrollHeight > all[i].clientHeight + 10) {
                    all[i].scrollTop = all[i].scrollHeight;
                    found.push({sh: all[i].scrollHeight, ch: all[i].clientHeight, tg: all[i].tagName});
                }
            }
            return found;
        }""")
        log(f"滚动容器: {json.dumps(scroll_info)}")
        pg.wait_for_timeout(1500)
        shot(pg, "13_style_subpanel_scrolled")

        # 滚动后扫描
        scan_region(pg, 80, 550, 100, 1200, "样式子面板滚动后")

        # ═══ 第六步: 查找颜色选择控件 (描边/阴影颜色) ═══
        log("\n" + "="*60)
        log("第六步: 颜色控件")

        color_elements = pg.evaluate("""() => {
            var r = [];
            var all = document.querySelectorAll('*');
            all.forEach(function(el) {
                var b = el.getBoundingClientRect();
                if (b.x > 80 && b.x < 550 && b.width >= 15 && b.height >= 15 && b.width < 80 && b.height < 80) {
                    var bg = window.getComputedStyle(el).backgroundColor;
                    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'rgba(255, 255, 255, 1)') {
                        r.push({tg: el.tagName, bg: bg, x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height)});
                    }
                }
            });
            return r.slice(0, 50);
        }""")
        log(f"颜色色块 ({len(color_elements)}):")
        for c in color_elements:
            log(f"  [{c['tg']}] ({c['x']},{c['y']}) {c['w']}x{c['h']} {c['bg']}")

        # ═══ 第七步: 检查是否有"间距"行或其他未探索的行 ═══
        log("\n" + "="*60)
        log("第七步: 查找右侧面板所有section行")

        # 先关闭样式子面板（如果打开了），然后找面板中的所有行
        # 点击面板外空白区域关闭子面板
        pg.mouse.click(970, 500)
        pg.wait_for_timeout(1500)

        # 重新扫描右侧面板区域，看是否有样式之外的其它行
        right_texts = page_text_in_area(pg, 1100, 1550, 400, 900)
        log(f"\n右侧面板全部文本 (关闭子面板后):")
        for item in right_texts:
            log(f"  [{item['tg']}] ({item['x']},{item['y']}) '{item['tx']}'")

        # 展开"字体"行, 先做个对比，确认样式子面板已经关闭
        shot(pg, "14_panel_rows_baseline")

        # ═══ 第八步: 检查右侧面板是否滚动后有更多行 ═══
        log("\n第八步: 滚动右侧面板...")
        right_scroll = pg.evaluate("""() => {
            var all = document.querySelectorAll('*');
            for (var i=0; i<all.length; i++) {
                var r = all[i].getBoundingClientRect();
                if (r.x > 1100 && r.x < 1550 && r.width > 100 && r.height > 100 &&
                    all[i].scrollHeight > all[i].clientHeight + 10) {
                    all[i].scrollTop = all[i].scrollHeight;
                    return {tg: all[i].tagName, sh: all[i].scrollHeight, ch: all[i].clientHeight};
                }
            }
            return null;
        }""")
        log(f"右侧面板滚动: {json.dumps(right_scroll)}")
        pg.wait_for_timeout(1000)

        if right_scroll:
            shot(pg, "15_right_panel_scrolled")
            right_texts2 = page_text_in_area(pg, 1100, 1550, 400, 900)
            log(f"\n右侧面板文本 (滚动后):")
            for item in right_texts2:
                log(f"  [{item['tg']}] ({item['x']},{item['y']}) '{item['tx']}'")

        # ═══ 第九步: 全页面最终扫描 ═══
        log("\n" + "="*60)
        log("第九步: 全页面交互元素最终扫描")
        scan_all_buttons(pg)

        # Body text 摘要
        log("\n========== Body 关键文本 ==========")
        body = pg.evaluate("() => document.body.innerText")
        # 只打印非空行
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        for l in lines[:80]:
            log(f"  {l}")

        shot(pg, "16_final_fullpage")
        ctx.close(); b.close()
        log("\n========== 探索完成 ==========")


def page_text_in_area(pg, x_min, x_max, y_min, y_max):
    """扫描区域内所有带文本的叶子节点"""
    return pg.evaluate("""([x_min, x_max, y_min, y_max]) => {
        var r = [];
        var seen = new Set();
        var all = document.querySelectorAll('*');
        all.forEach(function(el) {
            if (el.children.length > 0 && el.tagName !== 'OPTION') return;
            var t = (el.textContent || '').trim();
            if (!t || t.length > 150) return;
            var b = el.getBoundingClientRect();
            if (b.x >= x_min && b.x <= x_max && b.y >= y_min && b.y <= y_max &&
                b.width > 0 && b.height > 0) {
                var key = t + '|' + Math.round(b.x) + '|' + Math.round(b.y);
                if (seen.has(key)) return;
                seen.add(key);
                r.push({
                    tg: el.tagName, tx: t.slice(0, 100),
                    x: Math.round(b.x), y: Math.round(b.y),
                    w: Math.round(b.width), h: Math.round(b.height)
                });
            }
        });
        r.sort(function(a,b){return a.y-b.y||a.x-b.x;});
        return r;
    }""", [x_min, x_max, y_min, y_max])


if __name__ == "__main__":
    main()
