from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
anchor = '    allure_screenshot(page, "Outline色盘弹窗")'
idx = s.index(anchor)
new_tail = '''    allure_screenshot(page, "Outline色盘弹窗")
    assert page.locator("input.hexInput").is_visible()
    # 色盘应用品红 #ff00ff，作为后续取色的区分基准
    page.locator("input.hexInput").fill("#ff00ff")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    assert page.locator("input.hexInput").input_value() == "#ff00ff"
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    outline_palette_path = tmp_path / "outline_palette_magenta.png"
    page.screenshot(path=str(outline_palette_path))
    allure_screenshot(page, "Outline色盘应用品红")
    # 取色
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[6]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    outline_mode_path = tmp_path / "outline_picker_mode.png"
    page.screenshot(path=str(outline_mode_path))
    allure_screenshot(page, "Outline取色模式")
    assert pixel_diff_nonzero(str(outline_palette_path), str(outline_mode_path)) > 10000
    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255))
    assert target_info is not None
    assert target_dist > 80, f"Outline 取色目标与色盘品红太接近: dist={target_dist}"
    page.mouse.click(target_info[0], target_info[1])
    page.wait_for_timeout(1500)
    outline_applied_path = tmp_path / "outline_picker_applied.png"
    page.screenshot(path=str(outline_applied_path))
    allure_screenshot(page, "Outline取色应用后")
    assert pixel_diff_nonzero(str(outline_palette_path), str(outline_applied_path)) > 10000
'''
s = s[:idx] + new_tail
p.write_text(s, encoding='utf-8')
print('outline updated')
