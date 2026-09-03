from pathlib import Path
p = Path('artifacts/2026-08-30_pokecut_canvas_text_layer/impl.md')
s = p.read_text(encoding='utf-8')
s += '''
## 自修 round 5（色盘/取色颜色区分）
- Background：色盘改为蓝色 `#0000ff`；取色目标改为“与蓝色距离最大的画布像素”，并断言距离 > 80，确保取色颜色与色盘不同。
- Outline：色盘改为品红 `#ff00ff`；取色同样使用最大距离像素，断言与色盘颜色不同。
- 全量重跑 6 passed；重新生成 `reports/allure-report-matrix`。
'''
p.write_text(s, encoding='utf-8')
print('impl updated')
