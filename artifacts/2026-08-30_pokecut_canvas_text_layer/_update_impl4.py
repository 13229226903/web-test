from pathlib import Path
p = Path('artifacts/2026-08-30_pokecut_canvas_text_layer/impl.md')
s = p.read_text(encoding='utf-8')
s += '''
## 自修 round 4（Background 取色区分）
- 色盘应用色改为绿色 `#00ff00`（不再使用红色）。
- 取色前截图与色盘绿色应用态做像素 diff，断言取色模式确实进入。
- 从绿色应用态截图中寻找非绿色像素点作为取色目标，点击后截图并与绿色态做像素 diff，确保取色颜色与上一步不同。
- 全量重跑 6 passed；重新生成 `reports/allure-report-matrix`。
'''
p.write_text(s, encoding='utf-8')
print('impl updated')
