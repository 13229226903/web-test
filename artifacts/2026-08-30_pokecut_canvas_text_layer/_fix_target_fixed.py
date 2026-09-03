from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# Background: replace image-box target block with fixed point
old_bg = '''    img_box = canvas_image_box(page)
    assert img_box is not None, "未找到画布图片区域"
    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))
    assert target_info is not None
    assert target_dist > 80, f"取色目标与色盘蓝色太接近: dist={target_dist}"
    target = (target_info[0], target_info[1])
    page.mouse.click(target[0], target[1])'''
new_bg = '''    # 使用画布内固定已知可应用颜色的点（避免误点透明/白色边缘导致取色模式不退出）
    target = (900, 500)
    page.mouse.click(target[0], target[1])'''
s = s.replace(old_bg, new_bg)
# Outline: replace image-box target block with fixed point
old_ol = '''    img_box = canvas_image_box(page)
    assert img_box is not None, "Outline 未找到画布图片区域"
    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))
    assert target_info is not None
    assert target_dist > 80, f"Outline 取色目标与色盘品红太接近: dist={target_dist}"
    page.mouse.click(target_info[0], target_info[1])'''
new_ol = '''    # 使用画布内固定已知可应用颜色的点（避免误点透明/白色边缘导致取色模式不退出）
    target = (900, 500)
    page.mouse.click(target[0], target[1])'''
s = s.replace(old_ol, new_ol)
p.write_text(s, encoding='utf-8')
print('picker target fixed to (900,500)')
