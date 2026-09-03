from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
s = s.replace('page.locator("input.hexInput").fill("#00ff00")', 'page.locator("input.hexInput").fill("#0000ff")')
s = s.replace('assert page.locator("input.hexInput").input_value() == "#00ff00"', 'assert page.locator("input.hexInput").input_value() == "#0000ff"')
s = s.replace('allure_screenshot(page, "Background色盘应用绿色")', 'allure_screenshot(page, "Background色盘应用蓝色")')
old_target = '''    # 从色盘绿色应用态中找一个非绿色像素点作为取色目标，确保与上一步颜色不同
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
    page.mouse.click(target[0], target[1])'''
new_target = '''    # 从色盘蓝色应用态中找与蓝色距离最大的画布像素作为取色目标，确保取色颜色明显不同
    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255))
    assert target_info is not None
    assert target_dist > 80, f"取色目标与色盘蓝色太接近: dist={target_dist}"
    target = (target_info[0], target_info[1])
    page.mouse.click(target[0], target[1])'''
s = s.replace(old_target, new_target)
s = s.replace('assert nonzero_mode > 10000', 'assert nonzero_mode > 10000')
# update comment color mention
s = s.replace('色盘弹窗：应用绿色 #00ff00，作为后续取色的区分基准', '色盘弹窗：应用蓝色 #0000ff，作为后续取色的区分基准')
p.write_text(s, encoding='utf-8')
print('background updated to blue + distinct target')
