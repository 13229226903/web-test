import io
p = r"skills\ui-test-test-writing\SKILL.md"
s = io.open(p, encoding="utf-8").read()

old1 = "- 每条用例至少 1 张截图：结束态直接 `allure.attach(page.screenshot(), name=\"用例截图\", attachment_type=allure.attachment_type.PNG)`；不要每条用例都重复放首页加载截图。"
new1 = "- 每条用例的 Allure 步骤与截图按 cases.md 的 `步骤` / `截图点` 列一一对应：用 `allure.step` 描述步骤，在对应步骤内 attach 该步骤的截图；截图点不存在时才可省略该步骤截图。"

old2 = """## Allure 截图步骤规范

- 只有需要表达「操作边界/结果态」的明确步骤时，才用 `allure.step` 包裹并 attach；普通结束态截图按上面层级规范直接 attach，不额外包 step。
- 统一截图 helper 应保持行为简单：`conftest.allure_screenshot` 作为全页截图备选；常规用例结束态用 `page.screenshot()` 直接 attach，避免每条用例重复调用全页 helper。
- 异常 / 负向用例截图必须贴近异常提示或失败状态；预期提示未出现时，仍要在失败前截图当前态并让用例失败，不要用普通首屏截图伪装异常覆盖。
- 上传异常类用例优先走真实可见上传按钮 + `expect_file_chooser()`，不要直接 `set_input_files()` 到隐藏 input，避免绕过业务组件的前端校验 / toast 链路。"""
new2 = """## Allure 截图步骤规范

- 步骤名称来自 cases.md 的 `步骤` 列：`with allure.step("步骤描述"):` 包裹对应操作；该步骤的截图用 `allure.attach(page.screenshot(), name="<截图点>", attachment_type=allure.attachment_type.PNG)` 放在步骤内。
- 不要用一条固定「用例结束态」截图替代全部步骤；首页加载等公共动作也不是每条用例都放，按 cases.md 的截图点放置。
- 统一截图 helper 只作为全页截图备选（`conftest.allure_screenshot`）；常规步骤截图用 `page.screenshot()` 直接 attach。
- 异常 / 负向用例截图必须贴近异常提示或失败状态；预期提示未出现时，仍要在失败前截图当前态并让用例失败，不要用普通首屏截图伪装异常覆盖。
- 上传异常类用例优先走真实可见上传按钮 + `expect_file_chooser()`，不要直接 `set_input_files()` 到隐藏 input，避免绕过业务组件的前端校验 / toast 链路。"""

assert old1 in s
assert old2 in s
s = s.replace(old1, new1, 1)
s = s.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("patched SKILL screenshot step rules")
