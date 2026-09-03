from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
helper = '''\n\ndef canvas_image_box(page: Page):
    """返回画布中上传图片的可见区域，用于限制取色点击在图片内部。"""
    return page.evaluate("""() => {
        const imgs = [...document.querySelectorAll('img')];
        let best = null;
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            if (r.width > 50 && r.height > 50) {
                if (!best || r.width * r.height > best.w * best.h) {
                    best = {x: r.x, y: r.y, w: r.width, h: r.height};
                }
            }
        }
        return best;
    }""")

'''
marker = 'def test_text_001_entry_and_left_tools'
s = s.replace(marker, helper + marker)
p.write_text(s, encoding='utf-8')
print('canvas_image_box helper inserted')
