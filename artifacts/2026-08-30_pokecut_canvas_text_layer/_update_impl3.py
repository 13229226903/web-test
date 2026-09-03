from pathlib import Path
p = Path('artifacts/2026-08-30_pokecut_canvas_text_layer/impl.md')
s = p.read_text(encoding='utf-8')
s += '''
## 自修 round 3（优化用例 + Reflection 开关）
- 将 24 条重复路径用例合并为 6 条：入口/工具栏、选中/重开/Basic、Space、Reflection、Background、Outline。
- 修复 Reflection 四参数用例：先点击 Toggle 开启，再设置 4 个滑块并断言开关 class 与参数值。
- 全量重跑 `--alluredir=reports/allure-results-matrix`：6 passed；重新生成 `reports/allure-report-matrix`。
'''
p.write_text(s, encoding='utf-8')
print('impl updated')
