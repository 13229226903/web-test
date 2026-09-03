import io
p = r"skills\ui-test-test-case-design\SKILL.md"
s = io.open(p, encoding="utf-8").read()
old = "- L1/L2/L3/L5/L6 用例表列：`ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点`。"
new = """- L1/L2/L3/L5/L6 用例表列：`ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点`。
- `步骤` 列必须写编号可执行步骤（1. 2. 3.），每步与 test-writing 的 `allure.step` 及测试 docstring 的 `测试步骤` 一一对应。
- `截图点` 列写截图名，供对应步骤内 `allure.attach(page.screenshot(), name="<截图点>")` 使用。
- `测试点` 列即短标题，供 `@allure.title("L{N}-{NNN}: <测试点>")` 使用。"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("test-case-design SKILL optimized for steps/screenshot points")
