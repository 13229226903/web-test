from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# fix test_002
old2 = """    # Adjust 重开
    click_button_by_text(page, "Adjust", ymin=400, ymax=440, xmin=500)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() >= 1
"""
new2 = """    # 空白后重新添加文字以恢复选中态，再用 Move Up 制造“面板关闭但工具栏保留”，验证 Adjust 重开
    add_text(page)
    click_button_by_text(page, "Move Up", ymin=400, ymax=440, xmin=500)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() == 0
    click_button_by_text(page, "Adjust", ymin=400, ymax=440, xmin=500)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() >= 1
"""
s = s.replace(old2, new2)
p.write_text(s, encoding='utf-8')
print('test_002 fixed')
