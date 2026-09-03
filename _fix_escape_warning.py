from pathlib import Path
p=Path(r'D:\Test\web-test\tests\test_infinite_canvas_inspiration_debug.py')
s=p.read_text(encoding='utf-8')
s=s.replace('panel.locator("div.relative.z-\\[15\\].h-\\[2\\.75rem\\].px-\\[0\\.75rem\\]").first','panel.locator(r"div.relative.z-\\[15\\].h-\\[2\\.75rem\\].px-\\[0\\.75rem\\]").first')
p.write_text(s,encoding='utf-8')
