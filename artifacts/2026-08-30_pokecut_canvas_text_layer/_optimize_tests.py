from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
marker = '# ═══════════════════════════════════════════════════════════════\n# 用例实现'
head, sep, _ = s.partition(marker)
new_tests = '''# ═══════════════════════════════════════════════════════════════
# 用例实现（优化后：合并重复路径，6 条用例）
# ═══════════════════════════════════════════════════════════════

def test_text_001_entry_and_left_tools(page: Page, base_url: str):
    allure.dynamic.title("[L6][P0] 入口上传 + 左侧工具栏 + Add Text")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    url = enter_canvas(page, base_url)
    assert "/agent?pid=" in url
    for tool in ["image", "text", "sticker", "brush", "line", "shape", "layer"]:
        assert page.locator(f"button[data-tool-id='{tool}']").count() == 1
    add_text(page)
    body = page.locator("body").inner_text()
    for text in ["Adjust", "Move Up", "Move Down", "To Top", "To Bottom", "Flip h", "Flip v", "Delete", "Rotation"]:
        assert text in body


def test_text_002_select_reopen_tabs_basic(page: Page, base_url: str):
    allure.dynamic.title("[L2][P0] 选中/收起/重开 + Tab/Alignment/Font/Fill")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    enter_canvas(page, base_url)
    add_text(page)
    # 空白收起
    page.mouse.click(900, 300)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() == 0
    # Adjust 重开
    click_button_by_text(page, "Adjust", ymin=400, ymax=440, xmin=500)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() >= 1
    # Tab 切换
    click_button_by_text(page, "Basic", ymin=430, ymax=500)
    page.wait_for_timeout(800)
    # Alignment 点击
    page.evaluate("""() => {
        const ps=[...document.querySelectorAll('p')].filter(p=>p.textContent.trim()==='Alignment');
        for(const p of ps){const r=p.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const box=p.parentElement; if(box){const bs=[...box.querySelectorAll('button')]; bs[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}
        return false;
    }""")
    page.wait_for_timeout(800)
    # Font/Fill 存在
    assert page.locator("button", has_text="Font").count() >= 1
    assert page.locator("button", has_text="Fill").count() >= 1


def test_text_003_space(page: Page, base_url: str):
    allure.dynamic.title("[L5][P0] Space 单行禁用 + 两行 Height 生效")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    enter_canvas(page, base_url)
    add_text(page)
    click_button_by_text(page, "Space", ymin=480, ymax=820)
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Space单行Height禁用")
    sliders = get_section_sliders(page, "Space")
    assert sliders[0]["disabled"] is False
    assert sliders[1]["disabled"] is True
    make_two_line_text(page)
    allure_screenshot(page, "两行文字图层")
    click_button_by_text(page, "Space", ymin=480, ymax=820)
    page.wait_for_timeout(1000)
    sliders = get_section_sliders(page, "Space")
    assert sliders[1]["disabled"] is False
    before = panel_dimension_text(page)
    set_section_sliders(page, "Space", [0, 50])
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Space两行Height调整后")
    after = panel_dimension_text(page)
    assert before != after
    assert get_section_sliders(page, "Space")[1]["value"] == "50"


def test_text_004_reflection(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L5][P0] Reflection 四参数可调 + 实际反射效果")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
    enter_canvas(page, base_url)
    add_text(page)
    click_section_small(page, "Reflection")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Reflection展开四滑块")
    sliders = get_section_sliders(page, "Reflection")
    assert sliders is not None and len(sliders) == 4
    before = tmp_path / "reflection_before.png"
    page.screenshot(path=str(before))
    # 先开启开关
    assert click_section_toggle(page, "Reflection")
    page.wait_for_timeout(1000)
    cls = page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const toggles=[...row.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().width>=30&&b.getBoundingClientRect().width<=50); if(toggles[0]) return toggles[0].className;}}
        return '';
    }""")
    assert "bg-[#232323]" in cls
    # 四参数调整（开关开启后）
    vals = set_section_sliders(page, "Reflection", [20, 20, 20, 45])
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Reflection四参数调整后")
    assert vals == ["20", "20", "20", "45"]
    after = tmp_path / "reflection_after.png"
    page.screenshot(path=str(after))
    allure_screenshot(page, "Reflection开启效果")
    diff = ImageChops.difference(Image.open(before).convert("RGB"), Image.open(after).convert("RGB"))
    assert diff.getbbox() is not None
    nonzero = sum(1 for p in diff.getdata() if p != (0, 0, 0))
    assert nonzero > 10000


def test_text_005_background(page: Page, base_url: str):
    allure.dynamic.title("[L2][P0] Background 无填充/色盘/取色")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    enter_canvas(page, base_url)
    add_text(page)
    click_button_by_text(page, "Background", ymin=480, ymax=820)
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Background展开三按钮")
    content = page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return content.innerHTML;}}}
        return '';
    }""")
    assert "edit_icon_color_picker" in content
    # 色盘弹窗
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Background色盘弹窗")
    assert page.locator("input.hexInput").is_visible()
    page.locator("input.hexInput").fill("#ff0000")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    allure_screenshot(page, "Background色盘应用红色")
    assert page.locator("input.hexInput").input_value() == "#ff0000"
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    # 取色
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[2]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Background取色模式")
    page.mouse.click(900, 500)
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Background取色应用后")


def test_text_006_outline(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L2][P0] Outline Types/色盘/取色/四滑块/描边效果")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
    enter_canvas(page, base_url)
    add_text(page)
    click_section_small(page, "Outline")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline展开")
    # Toggle
    assert click_section_toggle(page, "Outline")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline开关开启")
    # Types 切换
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; bs[1].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}
        return false;
    }""")
    page.wait_for_timeout(800)
    allure_screenshot(page, "Outline Types切换")
    # 色盘弹窗
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Outline色盘弹窗")
    assert page.locator("input.hexInput").is_visible()
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    allure_screenshot(page, "Outline色盘关闭")
    # 取色
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[6]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline取色模式")
    page.mouse.click(900, 500)
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Outline取色应用后")
    # 四滑块
    vals = set_section_sliders(page, "Outline", [70, 20, 10, 30])
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline四滑块调整后")
    assert vals == ["70", "20", "10", "30"]
    # 描边效果（开启后像素 diff）
    before = tmp_path / "outline_before.png"
    page.screenshot(path=str(before))
    after = tmp_path / "outline_after.png"
    page.screenshot(path=str(after))
    diff = ImageChops.difference(Image.open(before).convert("RGB"), Image.open(after).convert("RGB"))
    assert diff.getbbox() is not None
    nonzero = sum(1 for p in diff.getdata() if p != (0, 0, 0))
    assert nonzero > 10000
'''
p.write_text(head + sep + new_tests, encoding='utf-8')
print('test file optimized to 6 tests')
