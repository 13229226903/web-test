"""无限画布 - Adjust 标签页（Reflection / Background / Outline）6 用例。"""

import os, glob, json, allure
from playwright.sync_api import Page, expect
from conftest import allure_screenshot, allure_screenshot_inline

def pick_test_image():
    img_dir = os.path.join(os.path.dirname(__file__), "..", "test_images")
    all_imgs = sorted(glob.glob(os.path.join(img_dir, "*")), key=lambda f: os.path.getsize(f))
    return os.path.abspath(all_imgs[min(2, len(all_imgs) - 1)])

def dismiss_overlay(page: Page):
    page.evaluate("""() => {
        var els=document.querySelectorAll('div[class*="fixed"]');
        for(var i=0;i<els.length;i++){var bg=window.getComputedStyle(els[i]).backgroundColor;
        if(bg&&bg.indexOf('rgba')>=0&&(bg.indexOf('0.3')>=0||bg.indexOf('0.5')>=0))els[i].remove();}
    }""")
    page.wait_for_timeout(1000)

def enter_canvas(page: Page, base_url: str, test_img: str):
    page.goto(f"{base_url}/create"); page.wait_for_timeout(4000)
    dismiss_overlay(page); dismiss_overlay(page)
    with page.expect_file_chooser() as fc_info:
        page.evaluate("""() => {var cards=document.querySelectorAll('[class*="cursor-pointer"]');
        for(var i=0;i<cards.length;i++){if(cards[i].textContent.indexOf('Start from a Photo')>=0)
        cards[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}}""")
    fc_info.value.set_files(test_img)
    page.wait_for_timeout(10000)
    assert "/agent" in page.url

def add_text(page: Page):
    dismiss_overlay(page)
    page.evaluate("""() => {var b=document.querySelector('button[data-tool-id="text"]');
    if(b)b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}""")
    page.wait_for_timeout(3000)

def switch_adjust(page: Page):
    page.evaluate("""() => {var btns=document.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='Adjust')
    btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));}}""")
    page.wait_for_timeout(1000)
    page.evaluate("""() => {var ps=document.querySelectorAll('[class*="scrollbar"]');
    for(var i=0;i<ps.length;i++){if(ps[i].scrollHeight>400)ps[i].scrollTop=ps[i].scrollHeight;}}""")
    page.wait_for_timeout(500)

def expand_section(page, name):
    """Playwright 点击 section name 展开。"""
    sec = _find_section_y(page, name)
    if sec:
        page.mouse.click(1200, sec['y'] + sec['h'] // 2)
    page.wait_for_timeout(2000)

def _find_section_y(page, name):
    """找到 section name 的 y 坐标。"""
    raw = page.evaluate("""(name) => {
        var els=document.querySelectorAll('button, span');
        for(var i=0;i<els.length;i++){
            var t=els[i].textContent.trim();
            if((t===name||t.indexOf(name+' ')===0)&&els[i].offsetWidth>20){
                var r=els[i].getBoundingClientRect();
                return JSON.stringify({y:Math.round(r.y),h:Math.round(r.height)});
            }
        }
        return 'null';
    }""", name)
    if raw == 'null': return None
    return json.loads(raw)

def _check_toggle_state(page, name):
    """检查 section 行内 toggle 按钮的状态。
    返回 'off' (灰色 OFF，className 含 d1d5db)、'on' (蓝色 ON) 或 'not_found'。
    """
    return page.evaluate("""(name) => {
        var els = document.querySelectorAll('button, span');
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            if ((t === name || t.indexOf(name + ' ') === 0) && els[i].offsetWidth > 20) {
                var row = els[i].parentElement.parentElement;
                if (!row) continue;
                var toggles = row.querySelectorAll('button[class*="rounded-full"]');
                for (var j = 0; j < toggles.length; j++) {
                    if (toggles[j].className.includes('d1d5db')) return 'off';
                }
                if (toggles.length > 0) return 'on';
            }
        }
        return 'not_found';
    }""", name)


def _check_dropdown_exists(page, name):
    """检查 section 行内是否存在 16×16 的下拉箭头按钮。"""
    return page.evaluate("""(name) => {
        var els = document.querySelectorAll('button, span');
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            if ((t === name || t.indexOf(name + ' ') === 0) && els[i].offsetWidth > 20) {
                var row = els[i].parentElement.parentElement;
                if (!row) continue;
                var btns = row.querySelectorAll('button');
                for (var j = 0; j < btns.length; j++) {
                    if (btns[j].offsetWidth === 16 && btns[j].offsetHeight === 16) return true;
                }
            }
        }
        return false;
    }""", name)


def _check_color_grid(page):
    """检查是否存在 grid-cols-5 颜色网格，返回网格中颜色按钮的数量。"""
    return page.evaluate("""() => {
        var grids = document.querySelectorAll('.grid-cols-5');
        for (var i = 0; i < grids.length; i++) {
            var btns = grids[i].querySelectorAll('button');
            if (btns.length >= 5) return btns.length;
        }
        return 0;
    }""")


def _check_sliders_in_section(page, name):
    """检查 section 参数面板中 x>700 的 input[type=range] 数量。"""
    return page.evaluate("""(name) => {
        var els = document.querySelectorAll('button, span, div');
        var container = null;
        for (var i = 0; i < els.length; i++) {
            var t = els[i].textContent.trim();
            if ((t === name || t.indexOf(name + ' ') === 0) && els[i].offsetWidth > 20) {
                container = els[i];
                for (var k = 0; k < 6; k++) container = container.parentElement;
                break;
            }
        }
        if (!container) return 0;
        var all = container.querySelectorAll('input[type="range"]');
        var count = 0;
        for (var j = 0; j < all.length; j++) {
            var rect = all[j].getBoundingClientRect();
            if (rect.x > 700 && rect.width > 50) count++;
        }
        return count;
    }""", name)


def click_toggle(page, name):
    """Playwright 点击 section 行内的 toggle（先找 y，再点 x=1360）。"""
    sec = _find_section_y(page, name)
    if not sec: return 'not_found'
    y = sec['y'] + sec['h'] // 2
    page.mouse.click(1360, y)
    page.wait_for_timeout(500)
    return 'toggled'

def click_dropdown(page, name):
    """Playwright 点击 section 行内的下拉箭头。先在行内找 16×16 按钮，再点其中心。"""
    raw = page.evaluate("""(name) => {
        var els=document.querySelectorAll('button, span');
        for(var i=0;i<els.length;i++){
            var t=els[i].textContent.trim();
            if((t===name||t.indexOf(name+' ')===0)&&els[i].offsetWidth>20){
                var row=els[i].parentElement.parentElement;
                if(!row)continue;
                var btns=row.querySelectorAll('button');
                for(var j=0;j<btns.length;j++){
                    if(btns[j].offsetWidth===16&&btns[j].offsetHeight===16){
                        var r=btns[j].getBoundingClientRect();
                        return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)});
                    }
                }
            }
        }
        return 'null';
    }""", name)
    if raw == 'null': return 'not_found'
    pos = json.loads(raw)
    page.mouse.click(pos['x'], pos['y'])
    page.wait_for_timeout(500)
    return 'dropdown'

def click_red(page):
    """Playwright 点击右侧面板中的红色颜色按钮。"""
    raw = page.evaluate("""() => {
        var all=document.querySelectorAll('button');
        var reds=[];
        for(var i=0;i<all.length;i++){
            var r=all[i].getBoundingClientRect();
            if(r.y<600||r.x<1100)continue;
            if(r.width>100||r.width<20)continue;
            var b=window.getComputedStyle(all[i]).backgroundColor;
            var m=b.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
            if(m){var rr=parseInt(m[1]),g=parseInt(m[2]),bb=parseInt(m[3]);
            reds.push(rr+','+g+','+bb);
            if(rr>120&&g<120&&bb<120&&rr>g&&rr>bb){
                var cx=r.x+r.width/2, cy=r.y+r.height/2;
                return JSON.stringify({x:Math.round(cx),y:Math.round(cy),c:rr+','+g+','+bb});
            }}
        }
        return 'null';
    }""")
    if raw == 'null': return 'no_red'
    pos = json.loads(raw)
    page.mouse.click(pos['x'], pos['y'])
    page.wait_for_timeout(500)
    return 'red_'+pos['c']

def drag_sliders(page, section_name, pct=0.5):
    """只拖拽 section_name 对应参数面板中的滑块（x≈1060, 排除 Space 的 x<700）。"""
    page.mouse.move(1300, 720)
    page.mouse.wheel(0, 500)
    page.wait_for_timeout(1000)

    # 找 section 容器，然后在其中找 x>700 的 input[type=range]
    raw = page.evaluate("""(name) => {
        var els=document.querySelectorAll('button, span, div');
        var container=null;
        for(var i=0;i<els.length;i++){
            var t=els[i].textContent.trim();
            if((t===name||t.indexOf(name+' ')===0)&&els[i].offsetWidth>20){
                container=els[i];
                for(var k=0;k<6;k++)container=container.parentElement;
                break;
            }
        }
        if(!container)return '[]';
        var all=container.querySelectorAll('input[type=\"range\"]');
        var r=[];
        for(var j=0;j<all.length;j++){
            var rect=all[j].getBoundingClientRect();
            // 只要 x>700 的（排除 Space 的 space-slider 在 x<700）
            if(rect.x>700&&rect.width>50){
                r.push({x:Math.round(rect.x),y:Math.round(rect.y),w:Math.round(rect.width),h:Math.round(rect.height)});
            }
        }
        return JSON.stringify(r);
    }""", section_name)
    sliders_json = json.loads(raw) if raw else []
    print(f"  drag_sliders[{section_name}]: found {len(sliders_json)} sliders: {sliders_json}")
    for sli in sliders_json:
        h = sli.get('h', 16)
        start_x = sli['x'] + 2
        target_x = sli['x'] + sli['w'] * pct
        cy = sli['y'] + h // 2
        page.mouse.move(start_x, cy)
        page.mouse.down()
        page.mouse.move(target_x, cy, steps=10)
        page.mouse.up()
        page.wait_for_timeout(300)

def setup(page, base_url):
    enter_canvas(page, base_url, pick_test_image())
    add_text(page)
    switch_adjust(page)

# ═══════════════════════════════
# Reflection
# ═══════════════════════════════
@allure.feature("Adjust标签页")
@allure.story("Reflection-反射")
@allure.title("TC-ADJ-001 [P1] 展开-默认关闭状态")
def test_adj_001_reflection_default(session_page: Page, base_url: str):
    page = session_page; setup(page, base_url)
    expand_section(page, "Reflection")
    # 验证 toggle 为灰色 OFF 状态（className 包含 d1d5db）
    toggle_state = _check_toggle_state(page, "Reflection")
    assert toggle_state == 'off', f"Reflection toggle 应为灰色 OFF 状态，实际: {toggle_state}"
    # 验证下拉箭头存在（行内 16×16 按钮）
    dropdown_exists = _check_dropdown_exists(page, "Reflection")
    assert dropdown_exists, "Reflection 行内应有 16×16 下拉箭头按钮"
    allure_screenshot(page, "01-Reflection-默认关闭")

@allure.feature("Adjust标签页")
@allure.story("Reflection-反射")
@allure.title("TC-ADJ-002 [P1] 开启反射-展开参数-拖拽滑块")
def test_adj_002_reflection_full(session_page: Page, base_url: str):
    page = session_page; setup(page, base_url)
    expand_section(page, "Reflection")
    click_dropdown(page, "Reflection")
    page.wait_for_timeout(500)
    toggle_result = click_toggle(page, "Reflection")
    assert toggle_result == 'toggled', f"Reflection toggle 点击失败: {toggle_result}"
    page.wait_for_timeout(1500)
    # 验证 toggle 已变为蓝色 ON 状态（不再含 d1d5db）
    toggle_state = _check_toggle_state(page, "Reflection")
    assert toggle_state == 'on', f"Reflection toggle 应为蓝色 ON 状态，实际: {toggle_state}"
    # 验证参数面板已展开（滑块出现）
    slider_count = _check_sliders_in_section(page, "Reflection")
    assert slider_count > 0, f"Reflection 参数面板展开后应有滑块控件，实际: {slider_count}"
    allure_screenshot(page, "02-Reflection-已开启-参数默认值")
    drag_sliders(page, "Reflection", 0.7)
    page.wait_for_timeout(500)
    # 验证拖拽后画布仍存在
    assert "/agent" in page.url, "拖拽滑块后画布应仍存在"
    allure_screenshot_inline(page, "03-Reflection-参数已拖拽")

@allure.feature("Adjust标签页")
@allure.story("Background-文字背景")
@allure.title("TC-ADJ-003 [P1] 展开-默认状态")
def test_adj_003_background_default(session_page: Page, base_url: str):
    page = session_page; setup(page, base_url)
    expand_section(page, "Background")
    # 验证 5 列颜色网格存在（grid-cols-5 中至少有 5 个颜色按钮）
    color_count = _check_color_grid(page)
    assert color_count >= 5, f"Background 颜色网格应有至少 5 个按钮，实际: {color_count}"
    allure_screenshot(page, "04-Background-默认状态")

@allure.feature("Adjust标签页")
@allure.story("Background-文字背景")
@allure.title("TC-ADJ-004 [P1] 选红色背景")
def test_adj_004_background_red(session_page: Page, base_url: str):
    page = session_page; setup(page, base_url)
    expand_section(page, "Background")
    red_result = click_red(page)
    assert red_result != 'no_red', "未找到红色背景色按钮，红色背景应被选中"
    page.wait_for_timeout(1000)
    allure_screenshot_inline(page, "05-Background-红色背景已应用")

@allure.feature("Adjust标签页")
@allure.story("Outline-描边")
@allure.title("TC-ADJ-005 [P1] 展开-默认关闭状态")
def test_adj_005_outline_default(session_page: Page, base_url: str):
    page = session_page; setup(page, base_url)
    expand_section(page, "Outline")
    # 验证 toggle 为灰色 OFF 状态（className 包含 d1d5db）
    toggle_state = _check_toggle_state(page, "Outline")
    assert toggle_state == 'off', f"Outline toggle 应为灰色 OFF 状态，实际: {toggle_state}"
    # 验证下拉箭头存在（行内 16×16 按钮）
    dropdown_exists = _check_dropdown_exists(page, "Outline")
    assert dropdown_exists, "Outline 行内应有 16×16 下拉箭头按钮"
    allure_screenshot(page, "06-Outline-默认关闭")

@allure.feature("Adjust标签页")
@allure.story("Outline-描边")
@allure.title("TC-ADJ-006 [P1] 开启描边-选红色-拖拽滑块")
def test_adj_006_outline_full(session_page: Page, base_url: str):
    page = session_page; setup(page, base_url)
    expand_section(page, "Outline")
    click_dropdown(page, "Outline")
    page.wait_for_timeout(500)
    toggle_result = click_toggle(page, "Outline")
    assert toggle_result == 'toggled', f"Outline toggle 点击失败: {toggle_result}"
    page.wait_for_timeout(1500)
    # 验证 toggle 已变为蓝色 ON 状态（不再含 d1d5db）
    toggle_state = _check_toggle_state(page, "Outline")
    assert toggle_state == 'on', f"Outline toggle 应为蓝色 ON 状态，实际: {toggle_state}"
    # 验证参数面板已展开（滑块出现）
    slider_count = _check_sliders_in_section(page, "Outline")
    assert slider_count > 0, f"Outline 参数面板展开后应有滑块控件，实际: {slider_count}"
    red_result = click_red(page)
    assert red_result != 'no_red', "未找到红色描边颜色按钮"
    page.wait_for_timeout(1000)
    allure_screenshot(page, "07-Outline-红色描边已应用-参数默认值")
    drag_sliders(page, "Outline", 0.5)
    page.wait_for_timeout(500)
    # 验证拖拽后画布仍存在
    assert "/agent" in page.url, "拖拽滑块后画布应仍存在"
    allure_screenshot_inline(page, "08-Outline-参数已拖拽")
