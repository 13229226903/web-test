from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# Background
old_bg = '''    # 使用画布内固定已知可应用颜色的点，避免误点透明/白色边缘导致取色模式不退出
    target = (900, 500)
    page.mouse.move(target[0], target[1])'''
new_bg = '''    # 从色盘蓝色应用态中找与蓝色距离最大的画布像素作为取色目标，确保颜色明显不同
    img_box = canvas_image_box(page)
    assert img_box is not None, "未找到画布图片区域"
    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))
    assert target_info is not None
    assert target_dist > 80, f"取色目标与色盘蓝色太接近: dist={target_dist}"
    target = (target_info[0], target_info[1])
    page.mouse.move(target[0], target[1])'''
s = s.replace(old_bg, new_bg)
# Outline
old_ol = '''    # 使用画布内固定已知可应用颜色的点，避免误点透明/白色边缘导致取色模式不退出
    target = (900, 500)
    page.mouse.move(target[0], target[1])'''
new_ol = '''    # 从色盘品红应用态中找与品红距离最大的画布像素作为取色目标，确保颜色明显不同
    img_box = canvas_image_box(page)
    assert img_box is not None, "Outline 未找到画布图片区域"
    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))
    assert target_info is not None
    assert target_dist > 80, f"Outline 取色目标与色盘品红太接近: dist={target_dist}"
    target = (target_info[0], target_info[1])
    page.mouse.move(target[0], target[1])'''
s = s.replace(old_ol, new_ol)
p.write_text(s, encoding='utf-8')
print('computed distinct targets restored')
