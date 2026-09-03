from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# Background
s = s.replace(
    '    page.mouse.click(target[0], target[1])\n    page.wait_for_timeout(1500)\n    applied_path = tmp_path / "bg_picker_applied.png"',
    '    page.mouse.move(target[0], target[1])\n    page.wait_for_timeout(300)\n    page.mouse.click(target[0], target[1])\n    page.wait_for_timeout(1500)\n    assert page.locator(".color-picker-wrapper").count() == 0, "取色后仍未退出取色模式"\n    applied_path = tmp_path / "bg_picker_applied.png"'
)
# Outline
s = s.replace(
    '    page.mouse.click(target_info[0], target_info[1])\n    page.wait_for_timeout(1500)\n    outline_applied_path = tmp_path / "outline_picker_applied.png"',
    '    page.mouse.move(target_info[0], target_info[1])\n    page.wait_for_timeout(300)\n    page.mouse.click(target_info[0], target_info[1])\n    page.wait_for_timeout(1500)\n    assert page.locator(".color-picker-wrapper").count() == 0, "Outline 取色后仍未退出取色模式"\n    outline_applied_path = tmp_path / "outline_picker_applied.png"'
)
p.write_text(s, encoding='utf-8')
print('picker move+click and exit assertion added')
