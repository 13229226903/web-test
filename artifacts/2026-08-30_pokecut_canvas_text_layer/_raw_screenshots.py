from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# Background mode
s = s.replace(
    '    mode_path = tmp_path / "bg_picker_mode.png"\n    page.screenshot(path=str(mode_path))\n    allure_screenshot(page, "Background取色模式")',
    '    mode_png = page.screenshot()\n    mode_path = tmp_path / "bg_picker_mode.png"\n    mode_path.write_bytes(mode_png)\n    allure.attach(mode_png, name="Background取色模式", attachment_type=allure.attachment_type.PNG)'
)
# Background applied
s = s.replace(
    '    applied_path = tmp_path / "bg_picker_applied.png"\n    page.screenshot(path=str(applied_path))\n    allure_screenshot(page, "Background取色应用后")',
    '    applied_png = page.screenshot()\n    applied_path = tmp_path / "bg_picker_applied.png"\n    applied_path.write_bytes(applied_png)\n    allure.attach(applied_png, name="Background取色应用后", attachment_type=allure.attachment_type.PNG)'
)
# Outline mode
s = s.replace(
    '    outline_mode_path = tmp_path / "outline_picker_mode.png"\n    page.screenshot(path=str(outline_mode_path))\n    allure_screenshot(page, "Outline取色模式")',
    '    outline_mode_png = page.screenshot()\n    outline_mode_path = tmp_path / "outline_picker_mode.png"\n    outline_mode_path.write_bytes(outline_mode_png)\n    allure.attach(outline_mode_png, name="Outline取色模式", attachment_type=allure.attachment_type.PNG)'
)
# Outline applied
s = s.replace(
    '    outline_applied_path = tmp_path / "outline_picker_applied.png"\n    page.screenshot(path=str(outline_applied_path))\n    allure_screenshot(page, "Outline取色应用后")',
    '    outline_applied_png = page.screenshot()\n    outline_applied_path = tmp_path / "outline_picker_applied.png"\n    outline_applied_path.write_bytes(outline_applied_png)\n    allure.attach(outline_applied_png, name="Outline取色应用后", attachment_type=allure.attachment_type.PNG)'
)
p.write_text(s, encoding='utf-8')
print('raw screenshots for picker mode/applied')
