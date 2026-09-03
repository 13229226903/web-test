from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
s = s.replace(
    '    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255))',
    '    img_box = canvas_image_box(page)\n    assert img_box is not None, "未找到画布图片区域"\n    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))'
)
s = s.replace(
    '    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255))',
    '    img_box = canvas_image_box(page)\n    assert img_box is not None, "Outline 未找到画布图片区域"\n    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))'
)
p.write_text(s, encoding='utf-8')
print('image box used for picker target')
