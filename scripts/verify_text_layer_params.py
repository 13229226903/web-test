"""
Pokecut Canvas Text Layer - 面板各参数操作步骤补充探索脚本
独立 chromium.launch() 模式，按 rule.md 规范编写。
探索内容:
  1. 删除图片图层，只保留文字图层
  2. 重新逐面板探索每个功能参数的具体操作步骤
  3. 每个操作截图记录
"""
import asyncio, json, os, sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://10.17.1.66:3102"
OUTPUT_DIR = Path("D:/Test/web-test/artifacts/2026-07-23_pokecut_text_layer")
SHOTS_DIR = OUTPUT_DIR / "shots2"
TEST_IMAGE = str(Path("D:/Test/web-test/test_images/3 - 副本.JPG").resolve())
EMAIL = "450832596@qq.com"
CODE = "123456"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def dismiss_overlay(page):
    await page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(o => {
            const bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes('rgba') && (bg.includes('0.3') || bg.includes('0.5'))) {
                o.remove();
            }
        });
    }""")
    await page.wait_for_timeout(1000)

async def dismiss_lang_prompt(page):
    """移除语言提示覆盖层(JS删除,不点击按钮以免切换语言)。"""
    await page.evaluate("""() => {
        // Remove any fixed overlay that's a language prompt
        document.querySelectorAll('div[class*="fixed"], div[style*="fixed"]').forEach(o => {
            const t = o.textContent || '';
            if (t.includes('browsing Simplified Chinese') || t.includes('Change to English')) {
                o.remove();
            }
        });
        // Also remove any full-viewport overlay (z-index high)
        document.querySelectorAll('div').forEach(o => {
            const r = o.getBoundingClientRect();
            if (r.width >= 1900 && r.height >= 1000 && r.x === 0 && r.y === 0) {
                const z = window.getComputedStyle(o).zIndex;
                if (z && parseInt(z) > 100) {
                    o.remove();
                }
            }
        });
    }""")
    await page.wait_for_timeout(1000)

async def dump_all_elements(page):
    return await page.evaluate("""() => {
        var result = { buttons: [], spans: [], sliders: [], divs: [] };
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            var r = btns[i].getBoundingClientRect();
            if (r.width > 0 && r.y < 2000) {
                result.buttons.push({
                    text: btns[i].textContent.trim().substring(0, 40),
                    x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height),
                    cls: btns[i].className.substring(0, 80),
                    dt: btns[i].getAttribute('data-tool-id') || ''
                });
            }
        }
        var spans = document.querySelectorAll('span');
        for (var i = 0; i < spans.length; i++) {
            var r = spans[i].getBoundingClientRect();
            var t = spans[i].textContent.trim();
            if (r.width > 0 && t.length > 0 && t.length < 30 && r.y < 2000 && r.x > 100) {
                result.spans.push({text: t, x: Math.round(r.x),
                    y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)});
            }
        }
        var ranges = document.querySelectorAll('input[type="range"]');
        for (var i = 0; i < ranges.length; i++) {
            var r = ranges[i].getBoundingClientRect();
            if (r.width > 0 && r.y < 2000) {
                result.sliders.push({
                    x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height),
                    cls: ranges[i].className.substring(0, 80),
                    val: ranges[i].value, min: ranges[i].min || '', max: ranges[i].max || ''
                });
            }
        }
        var texts = document.querySelectorAll('p, h2, h3');
        for (var i = 0; i < texts.length; i++) {
            var r = texts[i].getBoundingClientRect();
            var t = texts[i].textContent.trim();
            if (r.width > 0 && t.length > 0 && t.length < 40 && r.y < 2000) {
                result.divs.push({tag: texts[i].tagName, text: t,
                    x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height)});
            }
        }
        return result;
    }""")

async def find_smallest_matching(page, target_texts):
    """Find the smallest (most specific) element whose textContent matches any of target_texts.
    Returns {tag, cx, cy, w, h} or None."""
    return await page.evaluate("""(targets) => {
        var best = null;
        var bestArea = Infinity;
        var els = document.querySelectorAll('div, p, button');
        for (var i = 0; i < els.length; i++) {
            var r = els[i].getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) continue;
            if (r.width > 500 || r.height > 500) continue;  // skip large containers
            var t = els[i].textContent.trim();
            for (var j = 0; j < targets.length; j++) {
                if (t === targets[j] || (t.indexOf(targets[j]) === 0 && t.length < targets[j].length + 5)) {
                    var area = r.width * r.height;
                    if (area < bestArea) {
                        bestArea = area;
                        best = {
                            tag: els[i].tagName,
                            cx: Math.round(r.x + r.width/2),
                            cy: Math.round(r.y + r.height/2),
                            w: Math.round(r.width),
                            h: Math.round(r.height),
                            text: t.substring(0, 40)
                        };
                    }
                }
            }
        }
        return best ? JSON.stringify(best) : 'null';
    }""", target_texts)

async def main():
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}, locale="en-US"
        )
        page = await context.new_page()

        shot_num = [0]
        async def shot(name):
            shot_num[0] += 1
            num = str(shot_num[0]).zfill(2)
            path = SHOTS_DIR / f"{num}_{name}.png"
            await page.screenshot(path=str(path))
            log(f"  [shot {num}] {name}")
            return str(path)

        async def dump(label):
            e = await dump_all_elements(page)
            (SHOTS_DIR / f"dump_{label}.json").write_text(
                json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"  [dump] {label}: {len(e['buttons'])}b/{len(e['spans'])}s/{len(e['sliders'])}sl")
            return e

        # ============================================================
        # Phase 1: Login
        # ============================================================
        log("=" * 60)
        log("Phase 1: Login (English root page)")
        log("=" * 60)

        await page.goto(BASE_URL, timeout=120000)
        await page.wait_for_timeout(5000)

        await page.get_by_text("Log in", exact=True).first.click()
        await page.wait_for_timeout(3000)

        ei = page.locator('input[type="email"]')
        await ei.wait_for(state="visible", timeout=10000)
        await ei.fill(EMAIL)

        ci = page.locator('input[placeholder="Verification Code"]')
        await ci.wait_for(state="visible", timeout=5000)
        await ci.fill(CODE)

        await page.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.textContent.trim() === 'Log in' && b.offsetWidth > 200) {
                    b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        await page.wait_for_timeout(10000)

        await dismiss_overlay(page)
        await dismiss_overlay(page)
        await page.wait_for_timeout(2000)

        try:
            await page.locator("text='User8JY'").first.wait_for(state="visible", timeout=15000)
            log("  Login SUCCESS")
        except Exception:
            await page.screenshot(path=str(SHOTS_DIR / "login_failed.png"))
            log("  Login FAILED")
            await browser.close()
            return

        # ============================================================
        # Phase 2: /zh/create -> upload image -> /zh/agent
        # ============================================================
        log("=" * 60)
        log("Phase 2: /zh/create -> upload -> /zh/agent")
        log("=" * 60)

        await page.goto(f"{BASE_URL}/zh/create", timeout=60000)
        await page.wait_for_timeout(8000)

        # Dismiss everything
        await dismiss_overlay(page)
        await dismiss_overlay(page)
        await dismiss_lang_prompt(page)
        await page.wait_for_timeout(2000)

        await shot("zh_create_page")

        # Find the upload trigger element - look for smallest "从照片开始"
        upload_el = await find_smallest_matching(page, ["从照片开始", "Start from a Photo"])
        log(f"  Upload element: {upload_el}")

        if not upload_el or upload_el == 'null':
            # Fallback: dump all candidate divs
            candidates = await page.evaluate("""() => {
                var els = document.querySelectorAll('div, p, button');
                var r = [];
                for (var i = 0; i < els.length; i++) {
                    var rect = els[i].getBoundingClientRect();
                    var t = els[i].textContent.trim();
                    if (rect.width > 30 && rect.height > 10 && rect.width < 500 &&
                        (t.includes('照片') || t.includes('Photo'))) {
                        r.push({tag: els[i].tagName, text: t.substring(0, 60),
                            x: Math.round(rect.x), y: Math.round(rect.y),
                            w: Math.round(rect.width), h: Math.round(rect.height)});
                    }
                }
                return r;
            }""")
            log(f"  Photo candidates: {json.dumps(candidates, ensure_ascii=False)}")

            if candidates:
                c = candidates[0]
                upload_el = json.dumps({'cx': c['x'] + c['w']//2, 'cy': c['y'] + c['h']//2,
                                        'w': c['w'], 'h': c['h'], 'tag': c['tag']})
            else:
                log("  ERROR: No upload element found!")
                await browser.close()
                return

        el = json.loads(upload_el)

        # Trigger file chooser using dispatchEvent on the parent cursor-pointer card
        # (same approach as test_adjust_features.py which works reliably)
        async with page.expect_file_chooser() as fc_info:
            await page.evaluate("""() => {
                var cards = document.querySelectorAll('[class*="cursor-pointer"]');
                for (var i = 0; i < cards.length; i++) {
                    if (cards[i].textContent.indexOf('Start from a Photo') >= 0 ||
                        cards[i].textContent.indexOf('从照片开始') >= 0) {
                        cards[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        return;
                    }
                }
            }""")

        file_chooser = await fc_info.value
        await file_chooser.set_files(TEST_IMAGE)
        await page.wait_for_timeout(20000)
        log(f"  URL: {page.url}")

        await dismiss_overlay(page)
        await page.wait_for_timeout(5000)
        await shot("canvas_loaded")

        # Find the rendering area - look for the image dimension label first, then find container
        canvas_box = None

        for attempt in range(10):
            await page.wait_for_timeout(3000)

            # Find the image container by looking for the dimension label area
            # and the unique nested div structure at center of page
            container_info = await page.evaluate("""() => {
                // Strategy: find the div that contains the rendered image
                // Look for absolute-positioned divs in the center area with substantial size
                var divs = document.querySelectorAll('div.absolute');
                for (var i = 0; i < divs.length; i++) {
                    var r = divs[i].getBoundingClientRect();
                    // Image area: center-ish, large but not full screen
                    if (r.width > 200 && r.width < 600 && r.height > 300 && r.height < 800
                        && r.x > 300 && r.x < 1200 && r.y > 200 && r.y < 900) {
                        // This div should have a child with class "relative"
                        var relativeChild = divs[i].querySelector('div.relative');
                        if (relativeChild) {
                            return JSON.stringify({
                                x: Math.round(r.x), y: Math.round(r.y),
                                w: Math.round(r.width), h: Math.round(r.height),
                                hasRelative: true
                            });
                        }
                    }
                }
                // Fallback: find any div in the center area with these dimensions
                var allDivs = document.querySelectorAll('div');
                for (var j = 0; j < allDivs.length; j++) {
                    var rd = allDivs[j].getBoundingClientRect();
                    if (rd.width > 300 && rd.width < 500 && rd.height > 400 && rd.height < 700
                        && rd.x > 600 && rd.x < 1000 && rd.y > 250 && rd.y < 500) {
                        return JSON.stringify({
                            x: Math.round(rd.x), y: Math.round(rd.y),
                            w: Math.round(rd.width), h: Math.round(rd.height),
                            hasRelative: false
                        });
                    }
                }
                return 'null';
            }""")
            log(f"  Attempt {attempt+1}: container_info={container_info}")

            if container_info and container_info != 'null':
                ci = json.loads(container_info)
                canvas_box = {'x': ci['x'], 'y': ci['y'], 'width': ci['w'], 'height': ci['h']}
                log(f"  Found image container: {canvas_box}")
                break

        if not canvas_box:
            # Hard fallback to known position
            log("  Using hardcoded fallback position (778, 307, 364, 546)")
            canvas_box = {'x': 778, 'y': 307, 'width': 364, 'height': 546}
        await dump("canvas_initial")
        log(f"  Using canvas box: {canvas_box}")
        canvas_cx = canvas_box['x'] + canvas_box['width'] / 2
        canvas_cy = canvas_box['y'] + canvas_box['height'] / 2
        log(f"  Canvas center: ({canvas_cx:.0f}, {canvas_cy:.0f})")

        # ============================================================
        # Phase 3: Delete image layer
        # ============================================================
        log("=" * 60)
        log("Phase 3: Delete image layer")
        log("=" * 60)

        # Click canvas to select image
        await page.mouse.click(canvas_cx, canvas_cy)
        await page.wait_for_timeout(3000)
        await shot("canvas_image_selected")
        img_state = await dump("image_selected")

        # Find Delete button in toolbar area
        del_btns = [b for b in img_state['buttons']
                    if b['y'] > 380 and b['y'] < 520 and
                    ('Delete' in b['text'] or '删除' in b['text'])]
        log(f"  Delete btns in toolbar: {json.dumps(del_btns, ensure_ascii=False)}")

        if del_btns:
            db = del_btns[0]
            await page.mouse.click(db['x'] + db['w']/2, db['y'] + db['h']/2)
            await page.wait_for_timeout(2000)
            await shot("delete_image_layer")
            log("  Image layer deleted via Delete button")
        else:
            # Try keyboard
            await page.keyboard.press("Backspace")
            await page.wait_for_timeout(2000)
            await shot("backspace_delete")
            log("  Tried Backspace key")

        await dump("after_delete")

        # ============================================================
        # Phase 4: Add text layer
        # ============================================================
        log("=" * 60)
        log("Phase 4: Add text layer")
        log("=" * 60)

        # Activate text tool
        text_btn = page.locator("button[data-tool-id='text']")
        if await text_btn.count() > 0:
            tb = await text_btn.bounding_box()
            if tb:
                await page.mouse.click(tb['x'] + tb['width']/2, tb['y'] + tb['height']/2)
                await page.wait_for_timeout(3000)
                log("  Text tool active")
                await shot("text_tool_active")

        # Place text on canvas
        if canvas_box:
            await page.mouse.click(canvas_cx, canvas_cy)
            await page.wait_for_timeout(2000)

        await page.keyboard.type("Test", delay=100)
        await page.wait_for_timeout(1000)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)
        await shot("text_placed")

        # Deselect -> reselect for clean toolbar state
        # Click blank area
        await page.mouse.click(100, 500)
        await page.wait_for_timeout(2000)

        # Switch tool to reset
        img_btn2 = page.locator("button[data-tool-id='image']")
        if await img_btn2.count() > 0:
            ib2 = await img_btn2.bounding_box()
            if ib2:
                await page.mouse.click(ib2['x'] + ib2['width']/2, ib2['y'] + ib2['height']/2)
                await page.wait_for_timeout(1500)

        if await text_btn.count() > 0:
            tb2 = await text_btn.bounding_box()
            if tb2:
                await page.mouse.click(tb2['x'] + tb2['width']/2, tb2['y'] + tb2['height']/2)
                await page.wait_for_timeout(1500)

        # Click text to select
        if canvas_box:
            await page.mouse.click(canvas_cx, canvas_cy)
            await page.wait_for_timeout(3000)

        await shot("text_selected")
        text_state = await dump("text_selected")

        # ============================================================
        # Phase 5: Explore TOP toolbar -> right panel (Font/Style/Color)
        # ============================================================
        log("=" * 60)
        log("Phase 5: Top toolbar buttons")
        log("=" * 60)

        # Find top toolbar buttons - search wider y range (the text formatting toolbar
        # may appear at y~192 replacing the editor toolbar, or at y~422 from sync.md)
        top_btns_raw = await page.evaluate("""() => {
            var btns = document.querySelectorAll('button');
            var r = [];
            for (var i = 0; i < btns.length; i++) {
                var rect = btns[i].getBoundingClientRect();
                var t = btns[i].textContent.trim();
                // Text formatting buttons: Font/字体, Style/样式, Color/颜色, Align/对齐,
                // LineSpacing/行距, Flip/翻转, Delete/删除, Rotation/旋转
                var isTextBtn = (
                    t === 'Font' || t === '字体' ||
                    t === 'Style' || t === '样式' ||
                    t === 'Color' || t === '颜色' ||
                    t === 'Align' || t === '对齐' ||
                    t === 'Line Spacing' || t === '行距' ||
                    t === 'Flip H' || t === '水平翻转' ||
                    t === 'Flip V' || t === '垂直翻转' ||
                    t === 'Delete' || t === '删除' ||
                    t === 'Rotation' || t === '旋转'
                );
                if (isTextBtn && rect.x > 500) {
                    r.push({text: t, x: Math.round(rect.x), y: Math.round(rect.y),
                        w: Math.round(rect.width), h: Math.round(rect.height),
                        cx: Math.round(rect.x+rect.width/2), cy: Math.round(rect.y+rect.height/2)});
                }
            }
            return r;
        }""")
        top_btns_raw.sort(key=lambda b: b['x'])
        log(f"  Top toolbar ({len(top_btns_raw)} buttons): {json.dumps(top_btns_raw, ensure_ascii=False)}")

        label_map = {
            '字体':'Font','Font':'Font','样式':'Style','Style':'Style',
            '颜色':'Color','Color':'Color','对齐':'Align','Align':'Align',
            '行距':'LineSpacing','Line Spacing':'LineSpacing',
            '水平翻转':'FlipH','Flip H':'FlipH','垂直翻转':'FlipV','Flip V':'FlipV',
            '删除':'Delete','Delete':'Delete','旋转':'Rotation','Rotation':'Rotation'
        }

        for btn_info in top_btns_raw:
            key = label_map.get(btn_info['text'], btn_info['text'].replace(' ','_'))
            log(f"\n  --- {btn_info['text']} ({key}) ---")
            await page.mouse.click(btn_info['cx'], btn_info['cy'])
            await page.wait_for_timeout(3000)
            await shot(f"tb_{key.lower()}")
            after_dump = await dump(f"tb_{key.lower()}")

            # For Font/Style/Color: right panel appears, explore sub-sections
            if key in ('Font', 'Style', 'Color'):
                await explore_right_panel(page, key, shot, dump, log)

            # Dismiss before next
            await page.mouse.click(100, 100)
            await page.wait_for_timeout(1500)

            # Re-select text (except Delete which removes the layer)
            if key != 'Delete':
                if canvas_box:
                    await page.mouse.click(canvas_cx, canvas_cy)
                    await page.wait_for_timeout(2000)

        # ============================================================
        # Phase 6: Explore Adjust tab panel (Basic/Adjust)
        # ============================================================
        log("=" * 60)
        log("Phase 6: Basic/Adjust tabs")
        log("=" * 60)

        # Re-select text
        if canvas_box:
            await page.mouse.click(canvas_cx, canvas_cy)
            await page.wait_for_timeout(2000)

        await shot("pre_adjust")
        pre_dump = await dump("pre_adjust")

        # Find and click Adjust tab
        adjust_btn = page.locator("button:has-text('Adjust'), button:has-text('调整')")
        basic_btn = page.locator("button:has-text('Basic'), button:has-text('基础')")
        adj_count = await adjust_btn.count()
        bas_count = await basic_btn.count()
        log(f"  Adjust={adj_count}, Basic={bas_count}")

        panel_sections_found = False

        if adj_count > 0:
            ab = await adjust_btn.first.bounding_box()
            if ab:
                await page.mouse.click(ab['x'] + ab['width']/2, ab['y'] + ab['height']/2)
                await page.wait_for_timeout(2000)
                await shot("adjust_tab")
                adj_dump = await dump("adjust_tab")

                # Scroll panel
                await page.mouse.move(1300, 720)
                await page.mouse.wheel(0, 500)
                await page.wait_for_timeout(1000)

                # Explore: Space(间距), Reflection(反射), Background(背景), Outline(描边)
                sections = [
                    ('Space', '间距'),
                    ('Reflection', '反射'),
                    ('Background', '背景'),
                    ('Outline', '描边'),
                ]

                for sec_en, sec_cn in sections:
                    log(f"\n  >>> {sec_en} ({sec_cn}) <<<")
                    await explore_adjust_section(page, sec_en, sec_cn, shot, dump, log)

                panel_sections_found = True

        if not panel_sections_found:
            # Try finding sections by scanning right area
            log("  Scanning right panel elements...")
            right_els = await page.evaluate("""() => {
                var els = document.querySelectorAll('button, span, p');
                var r = [];
                for (var i = 0; i < els.length; i++) {
                    var rect = els[i].getBoundingClientRect();
                    var t = els[i].textContent.trim();
                    if (rect.x > 800 && rect.y > 200 && rect.y < 900 && t.length > 0 && t.length < 30) {
                        r.push({tag: els[i].tagName, text: t,
                            x: Math.round(rect.x), y: Math.round(rect.y),
                            w: Math.round(rect.width), h: Math.round(rect.height)});
                    }
                }
                return r;
            }""")
            log(f"  Right elements: {json.dumps(right_els, ensure_ascii=False, indent=2)}")

        # ============================================================
        # Phase 7: Final shot
        # ============================================================
        log("=" * 60)
        log("Phase 7: Final state")
        log("=" * 60)
        await shot("final_full")

        log(f"\n  DONE! {shot_num[0]} screenshots saved to {SHOTS_DIR}")
        await browser.close()


async def explore_right_panel(page, key, shot, dump, log):
    """Explore right property panel sub-sections opened by Font/Style/Color."""
    log(f"    Exploring right panel for {key}...")

    # Dump current right panel contents
    right = await page.evaluate("""() => {
        var els = document.querySelectorAll('button, span, p, input[type="range"]');
        var r = [];
        for (var i = 0; i < els.length; i++) {
            var rect = els[i].getBoundingClientRect();
            var t = els[i].textContent.trim().substring(0, 40);
            if (rect.x > 1100 && rect.y > 400 && rect.y < 800 && rect.width > 0) {
                r.push({tag: els[i].tagName, type: els[i].type || '', text: t,
                    x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height)});
            }
        }
        return r;
    }""")
    log(f"    Right panel elements: {json.dumps(right, ensure_ascii=False, indent=2)}")

    # Click expandable sections in order
    expander_ys = [461, 521, 643]  # Row 1 buttons, Font expander, Style expander
    for i, ey in enumerate(expander_ys):
        log(f"      Click expander at y={ey}")
        await page.mouse.click(1332, ey)
        await page.wait_for_timeout(2000)
        await shot(f"rp_{key}_expand_{i}")
        expanded = await page.evaluate("""() => {
            var els = document.querySelectorAll('button, span, input[type="range"]');
            var r = [];
            for (var i = 0; i < els.length; i++) {
                var rect = els[i].getBoundingClientRect();
                var t = els[i].textContent.trim().substring(0, 40);
                if (rect.x > 1130 && rect.y > 470 && rect.y < 750 && rect.width > 0) {
                    r.push({tag: els[i].tagName, type: els[i].type || '', text: t,
                        x: Math.round(rect.x), y: Math.round(rect.y),
                        w: Math.round(rect.width), h: Math.round(rect.height)});
                }
            }
            return r;
        }""")
        log(f"        Expanded items: {json.dumps(expanded, ensure_ascii=False, indent=2)}")

        # If font grid appeared, click font items
        font_candidates = [e for e in expanded if e['w'] > 60 and e['w'] < 200]
        if font_candidates:
            log(f"        Found {len(font_candidates)} clickable items")

    # Drag sliders in the right panel
    sliders_raw = await page.evaluate("""() => {
        var sl = document.querySelectorAll('input[type="range"]');
        var r = [];
        for (var i = 0; i < sl.length; i++) {
            var rect = sl[i].getBoundingClientRect();
            if (rect.x > 1100 && rect.width > 50) {
                r.push({x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height),
                    v: sl[i].value});
            }
        }
        return r;
    }""")
    log(f"    Right panel sliders: {json.dumps(sliders_raw, ensure_ascii=False)}")

    for si, sl in enumerate(sliders_raw):
        cy = sl['y'] + sl['h'] / 2
        await page.mouse.move(sl['x'] + 5, cy)
        await page.mouse.down()
        await page.mouse.move(sl['x'] + sl['w'] * 0.75, cy, steps=10)
        await page.mouse.up()
        await page.wait_for_timeout(500)
        await shot(f"rp_{key}_slider_{si}")

    # Check for color grids
    color_btns = await page.evaluate("""() => {
        var grids = document.querySelectorAll('.grid-cols-5, [class*="grid-cols"]');
        var r = [];
        for (var i = 0; i < grids.length; i++) {
            var btns = grids[i].querySelectorAll('button');
            for (var j = 0; j < btns.length; j++) {
                var rect = btns[j].getBoundingClientRect();
                var bg = window.getComputedStyle(btns[j]).backgroundColor;
                if (rect.y > 400 && rect.width > 20 && rect.width < 60) {
                    r.push({x: Math.round(rect.x+rect.width/2), y: Math.round(rect.y+rect.height/2), bg: bg});
                }
            }
        }
        return r;
    }""")
    log(f"    Color buttons: {len(color_btns)}")
    if color_btns:
        for ci, cb in enumerate(color_btns[:5]):
            await page.mouse.click(cb['x'], cb['y'])
            await page.wait_for_timeout(600)
            await shot(f"rp_{key}_color_{ci}")


async def explore_adjust_section(page, sec_en, sec_cn, shot, dump, log):
    """Explore one section in the Adjust tab (Space/Reflection/Background/Outline)."""
    # Find the section span/button
    found = await page.evaluate("""(names) => {
        var arr = JSON.parse(names);
        var els = document.querySelectorAll('button, span');
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            for (var j = 0; j < arr.length; j++) {
                if ((t === arr[j] || t.indexOf(arr[j]) === 0) && els[i].offsetWidth > 20) {
                    var r = els[i].getBoundingClientRect();
                    return JSON.stringify({
                        text: t, tag: els[i].tagName,
                        x: Math.round(r.x + r.width/2),
                        y: Math.round(r.y + r.height/2)
                    });
                }
            }
        }
        return 'null';
    }""", json.dumps([sec_en, sec_cn]))

    if not found or found == 'null':
        log(f"    Section '{sec_en}' NOT FOUND")
        return

    fi = json.loads(found)
    log(f"    Found: {fi}")

    # Click section name to expand it
    await page.mouse.click(fi['x'], fi['y'])
    await page.wait_for_timeout(2000)
    await shot(f"adj_{sec_en.lower()}_open")

    # Find dropdown arrow (16x16 button)
    dd_raw = await page.evaluate("""(name) => {
        var els = document.querySelectorAll('button, span');
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            if ((t === name || t.indexOf(name) === 0) && els[i].offsetWidth > 20) {
                var row = els[i].parentElement.parentElement;
                if (!row) continue;
                var btns = row.querySelectorAll('button');
                for (var j = 0; j < btns.length; j++) {
                    if (btns[j].offsetWidth === 16 && btns[j].offsetHeight === 16) {
                        var r = btns[j].getBoundingClientRect();
                        return JSON.stringify({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                    }
                }
            }
        }
        return 'null';
    }""", sec_en)

    if dd_raw and dd_raw != 'null':
        dp = json.loads(dd_raw)
        # Click dropdown first (per rule.md)
        await page.mouse.click(dp['x'], dp['y'])
        await page.wait_for_timeout(1000)
        await shot(f"adj_{sec_en.lower()}_dropdown")

    # Find and click toggle
    tg_raw = await page.evaluate("""(name) => {
        var els = document.querySelectorAll('button, span');
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            if ((t === name || t.indexOf(name) === 0) && els[i].offsetWidth > 20) {
                var row = els[i].parentElement.parentElement;
                if (!row) continue;
                var toggles = row.querySelectorAll('button[class*="rounded-full"]');
                for (var j = 0; j < toggles.length; j++) {
                    var r = toggles[j].getBoundingClientRect();
                    return JSON.stringify({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)});
                }
            }
        }
        return 'null';
    }""", sec_en)

    if tg_raw and tg_raw != 'null':
        # Check current toggle state before clicking
        tg_state = await page.evaluate("""(name) => {
            var els = document.querySelectorAll('button, span');
            for (var i = 0; i < els.length; i++) {
                var t = els[i].textContent.trim();
                if ((t === name || t.indexOf(name) === 0) && els[i].offsetWidth > 20) {
                    var row = els[i].parentElement.parentElement;
                    if (!row) continue;
                    var toggles = row.querySelectorAll('button[class*="rounded-full"]');
                    for (var j = 0; j < toggles.length; j++) {
                        return toggles[j].className.includes('d1d5db') ? 'off' : 'on';
                    }
                }
            }
            return 'unknown';
        }""", sec_en)
        log(f"    Toggle state before click: {tg_state}")

        tp = json.loads(tg_raw)
        await page.mouse.click(tp['x'], tp['y'])
        await page.wait_for_timeout(1500)
        await shot(f"adj_{sec_en.lower()}_toggled")

    # Drag sliders in section
    sliders_in_sec = await page.evaluate("""(name) => {
        var els = document.querySelectorAll('button, span, div');
        var container = null;
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            if ((t === name || t.indexOf(name) === 0) && els[i].offsetWidth > 20) {
                container = els[i];
                for (var k = 0; k < 6; k++) container = container.parentElement;
                break;
            }
        }
        if (!container) return [];
        var all = container.querySelectorAll('input[type="range"]');
        var r = [];
        for (var j = 0; j < all.length; j++) {
            var rect = all[j].getBoundingClientRect();
            if (rect.x > 700 && rect.width > 50) {
                r.push({x: Math.round(rect.x), y: Math.round(rect.y),
                    w: Math.round(rect.width), h: Math.round(rect.height), v: all[j].value});
            }
        }
        return r;
    }""", sec_en)
    log(f"    Section sliders: {json.dumps(sliders_in_sec, ensure_ascii=False)}")

    for si, sl in enumerate(sliders_in_sec):
        cy = sl['y'] + sl['h'] / 2
        await page.mouse.move(sl['x'] + 5, cy)
        await page.mouse.down()
        await page.mouse.move(sl['x'] + sl['w'] * 0.7, cy, steps=10)
        await page.mouse.up()
        await page.wait_for_timeout(300)
        await shot(f"adj_{sec_en.lower()}_slider{si}")

    # Check for red color in color grid (for Background/Outline)
    red_raw = await page.evaluate("""(name) => {
        var all = document.querySelectorAll('button');
        for (var i = 0; i < all.length; i++) {
            var r = all[i].getBoundingClientRect();
            if (r.y < 600 || r.x < 800) continue;
            if (r.width > 100 || r.width < 20) continue;
            var b = window.getComputedStyle(all[i]).backgroundColor;
            var m = b.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
            if (m) {
                var rr = parseInt(m[1]), g = parseInt(m[2]), bb = parseInt(m[3]);
                if (rr > 120 && g < 120 && bb < 120 && rr > g && rr > bb) {
                    return JSON.stringify({x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2), bg: b});
                }
            }
        }
        return 'null';
    }""", sec_en)

    if red_raw and red_raw != 'null':
        rp = json.loads(red_raw)
        await page.mouse.click(rp['x'], rp['y'])
        await page.wait_for_timeout(1000)
        await shot(f"adj_{sec_en.lower()}_red")


if __name__ == "__main__":
    asyncio.run(main())
