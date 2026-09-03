from pathlib import Path
p = Path('artifacts/2026-08-30_pokecut_canvas_text_layer/impl.md')
s = p.read_text(encoding='utf-8')
s += '''
## 自修 round 2（截图补全）
- 问题：多个用例只通过 enter_canvas/add_text 的公共截图展示，缺少关键最终态截图（色盘弹窗、Reflection/Outline 效果、Space/Reflection 展开等）。
- 原因：操作和断言实际已执行成功，但测试代码未在关键动作后调用 `allure_screenshot(page, ...)`，导致报告只有前置截图。
- 修复：为相关用例补充最终态 Allure 截图步骤；collect-only 仍 24 tests；全量重跑 `--alluredir=reports/allure-results-matrix` 24 passed；重新生成 `reports/allure-report-matrix`。
'''
p.write_text(s, encoding='utf-8')
print('impl updated')
