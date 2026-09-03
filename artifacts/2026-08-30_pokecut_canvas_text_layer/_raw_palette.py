from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# Background palette applied raw
s = s.replace(
    '    palette_path = tmp_path / "bg_palette_green.png"\n    page.screenshot(path=str(palette_path))\n    allure_screenshot(page, "Background色盘应用蓝色")',
    '    palette_png = page.screenshot()\n    palette_path = tmp_path / "bg_palette_blue.png"\n    palette_path.write_bytes(palette_png)\n    allure.attach(palette_png, name="Background色盘应用蓝色", attachment_type=allure.attachment_type.PNG)'
)
# Outline palette applied raw
s = s.replace(
    '    outline_palette_path = tmp_path / "outline_palette_magenta.png"\n    page.screenshot(path=str(outline_palette_path))\n    allure_screenshot(page, "Outline色盘应用品红")',
    '    outline_palette_png = page.screenshot()\n    outline_palette_path = tmp_path / "outline_palette_magenta.png"\n    outline_palette_path.write_bytes(outline_palette_png)\n    allure.attach(outline_palette_png, name="Outline色盘应用品红", attachment_type=allure.attachment_type.PNG)'
)
p.write_text(s, encoding='utf-8')
print('palette applied screenshots raw')
