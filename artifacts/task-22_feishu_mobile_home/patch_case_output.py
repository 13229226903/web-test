import io
p = r"skills\ui-test-test-case-design\SKILL.md"
s = io.open(p, encoding="utf-8").read()
old = """## 输出格式
- 表格用 markdown 表格；步骤为可执行清单；期望可断言，避免“正常显示”类模糊词。
- 上传 / 生成 / credits 用例写明登录、环境顺序、数据与授权要求。
- AI 审查列为“是”时写明确视觉判断目标；Allure 用中文标题 / 描述 / 步骤并标注 Layer。"""
new = """## 输出格式
- 表格用 markdown 表格；`步骤` 列为编号可执行清单（1. 2. 3.），每步对应 test-writing 的 `allure.step` 与测试 docstring 的 `测试步骤`。
- `截图点` 列写截图名，供对应步骤内 `allure.attach(page.screenshot(), name="<截图点>")` 使用；`测试点` 列即短标题，供 `@allure.title("L{N}-{NNN}: <测试点>")` 使用。
- 期望可断言，避免“正常显示”类模糊词。
- 上传 / 生成 / credits 用例写明登录、环境顺序、数据与授权要求。
- AI 审查列为“是”时写明确视觉判断目标；Allure 用中文标题 / 描述 / 步骤并标注 Layer。"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("test-case-design SKILL 输出格式已更新")
