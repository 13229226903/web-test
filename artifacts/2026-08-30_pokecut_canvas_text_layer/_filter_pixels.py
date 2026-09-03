from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
old = '''        for x in range(x0, x1, 2):
            r, g, b = img.getpixel((x, y))
            dist = ((r - ref_rgb[0]) ** 2 + (g - ref_rgb[1]) ** 2 + (b - ref_rgb[2]) ** 2) ** 0.5
            if dist > best_dist:
                best_dist = dist
                best = (x, y, (r, g, b))'''
new = '''        for x in range(x0, x1, 2):
            r, g, b = img.getpixel((x, y))
            # 忽略接近白色/黑色的无效取色点
            if max(r, g, b) > 245 or max(r, g, b) < 20:
                continue
            dist = ((r - ref_rgb[0]) ** 2 + (g - ref_rgb[1]) ** 2 + (b - ref_rgb[2]) ** 2) ** 0.5
            if dist > best_dist:
                best_dist = dist
                best = (x, y, (r, g, b))'''
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print('filtered white/black in most_distinct_pixel')
