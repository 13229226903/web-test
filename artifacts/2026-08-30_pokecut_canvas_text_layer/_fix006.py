from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
start = s.index('def test_text_006_outline')
new_func = '''def test_text_006_outline(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L2][P0] Outline Types/色盘/取色/四滑块/描边效果")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
    enter_canvas(page, base_url)
    add_text(page)
    click_section_small(page, "Outline")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline展开")
    # 描边效果：先记录开启前后
    before = tmp_path / "outline_before.png"
    page.screenshot(path=str(before))
    assert click_section_toggle(page, "Outline")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline开关开启")
    after = tmp_path / "outline_after.png"
    page.screenshot(path=str(after))
    diff = ImageChops.difference(Image.open(before).convert("RGB"), Image.open(after).convert("RGB"))
    assert diff.getbbox() is not None
    nonzero = sum(1 for p in diff.getdata() if p != (0, 0, 0))
    assert nonzero > 10000
    # Types 切换
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; bs[1].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}
        return false;
    }""")
    page.wait_for_timeout(800)
    allure_screenshot(page, "Outline Types切换")
    # 四滑块
    vals = set_section_sliders(page, "Outline", [70, 20, 10, 30])
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline四滑块调整后")
    assert vals == ["70", "20", "10", "30"]
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
'''
s = s[:start] + new_func
p.write_text(s, encoding='utf-8')
print('test_006 rewritten')
