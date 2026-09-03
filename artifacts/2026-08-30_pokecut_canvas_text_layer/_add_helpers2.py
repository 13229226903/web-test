from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
helper = '''\n\ndef pixel_diff_nonzero(path1, path2):
    from PIL import Image, ImageChops
    diff = ImageChops.difference(Image.open(path1).convert("RGB"), Image.open(path2).convert("RGB"))
    if diff.getbbox() is None:
        return 0
    return sum(1 for px in diff.getdata() if px != (0, 0, 0))


def most_distinct_pixel(path, ref_rgb, x0=700, x1=1000, y0=250, y1=800):
    """在画布区域找与参考色距离最大的像素点，确保取色颜色与色盘颜色区分明显。"""
    from PIL import Image
    img = Image.open(path).convert("RGB")
    best = None
    best_dist = -1
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            r, g, b = img.getpixel((x, y))
            dist = ((r - ref_rgb[0]) ** 2 + (g - ref_rgb[1]) ** 2 + (b - ref_rgb[2]) ** 2) ** 0.5
            if dist > best_dist:
                best_dist = dist
                best = (x, y, (r, g, b))
    return best, best_dist

'''
marker = 'def test_text_001_entry_and_left_tools'
s = s.replace(marker, helper + marker)
p.write_text(s, encoding='utf-8')
print('helpers inserted')
