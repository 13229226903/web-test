from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
old = 'assert "Chat to edit" in page.locator("body").inner_text()'
new = 'body = page.locator("body").inner_text()\n    assert "Enhance" in body'
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print('fixed')
