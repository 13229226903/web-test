from pathlib import Path
p = Path('artifacts/regression_registry.md')
s = p.read_text(encoding='utf-8')
row = '| 画布页文字功能 | http://10.17.1.66:3001/create → /agent?pid=<uuid> | stable_regression | 2026-08-30_pokecut_canvas_text_layer | tests/test_infinite_canvas_text_layer_v2.py | archive/infinite_canvas/test_infinite_canvas_text_layer_v2.py | page_map/pokecut/infinite_canvas_text_layer_v2.yaml | artifacts/2026-08-30_pokecut_canvas_text_layer/sync.md | artifacts/2026-08-30_pokecut_canvas_text_layer/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-08-31 6 passed in 296s；`python -m pytest tests/test_infinite_canvas_text_layer_v2.py -q` | 测试服 http://10.17.1.66:3001；PC 1920x1080 en-US；匿名上传可用；素材 test_images/低分辨率.JPG | 优化去重 6 用例；Reflection/Outline 像素 diff 断言效果；色盘弹窗应用后需再次点击色盘按钮关闭 |\n'
if not s.endswith('\n'):
    s += '\n'
s += row
p.write_text(s, encoding='utf-8')
print('registry updated')
