from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
start = s.index('def test_text_005_background')
end = s.index('def test_text_006_outline')
new_func = '''def test_text_005_background(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L2][P0] Background 无填充/色盘/取色")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
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
    # 色盘弹窗：应用绿色 #00ff00，作为后续取色的区分基准
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Background色盘弹窗")
    assert page.locator("input.hexInput").is_visible()
    page.locator("input.hexInput").fill("#00ff00")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    assert page.locator("input.hexInput").input_value() == "#00ff00"
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    palette_path = tmp_path / "bg_palette_green.png"
    page.screenshot(path=str(palette_path))
    allure_screenshot(page, "Background色盘应用绿色")
    # 取色按钮：进入取色模式
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[2]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    mode_path = tmp_path / "bg_picker_mode.png"
    page.screenshot(path=str(mode_path))
    allure_screenshot(page, "Background取色模式")
    # 断言确实进入取色状态（画面/光标与色盘应用态有差异）
    diff_mode = ImageChops.difference(Image.open(palette_path).convert("RGB"), Image.open(mode_path).convert("RGB"))
    assert diff_mode.getbbox() is not None
    nonzero_mode = sum(1 for px in diff_mode.getdata() if px != (0, 0, 0))
    assert nonzero_mode > 10000
    # 从色盘绿色应用态中找一个非绿色像素点作为取色目标，确保与上一步颜色不同
    img = Image.open(palette_path).convert("RGB")
    target = None
    for y in range(250, 800, 5):
        for x in range(700, 1000, 5):
            r, g, b = img.getpixel((x, y))
            if not (g > r + 40 and g > b + 40):
                target = (x, y)
                break
        if target:
            break
    if target is None:
        target = (900, 500)
    page.mouse.click(target[0], target[1])
    page.wait_for_timeout(1500)
    applied_path = tmp_path / "bg_picker_applied.png"
    page.screenshot(path=str(applied_path))
    allure_screenshot(page, "Background取色应用后")
    # 断言取色应用后的画面与色盘绿色应用态不同（颜色已区分）
    diff_applied = ImageChops.difference(Image.open(palette_path).convert("RGB"), Image.open(applied_path).convert("RGB"))
    assert diff_applied.getbbox() is not None
    nonzero_applied = sum(1 for px in diff_applied.getdata() if px != (0, 0, 0))
    assert nonzero_applied > 10000

'''
s = s[:start] + new_func + s[end:]
p.write_text(s, encoding='utf-8')
print('test_005 rewritten')
