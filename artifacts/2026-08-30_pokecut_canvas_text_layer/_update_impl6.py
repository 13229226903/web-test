from pathlib import Path
p = Path('artifacts/2026-08-30_pokecut_canvas_text_layer/impl.md')
s = p.read_text(encoding='utf-8')
s += '''
## 自修 round 6（取色截图时机与色盘弹窗关闭）
- 根因：色盘弹窗在 Enter 应用后 Escape 无法关闭，导致后续取色点击实际未退出取色模式。
- 修复：应用 hex 后再次点击色盘按钮关闭弹窗；取色模式/取色应用截图改用 `page.screenshot()` + `allure.attach`，避免 `allure_screenshot` 改 viewport 破坏取色交互。
- 取色目标改为画布图片区域中与色盘颜色距离最大的有效像素点，并断言退出取色模式与像素 diff。
- 全量重跑 6 passed；重新生成 `reports/allure-report-matrix`。
'''
p.write_text(s, encoding='utf-8')
print('impl updated')
