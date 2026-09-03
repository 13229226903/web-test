import io
p = r"skills\ui-test-test-writing\SKILL.md"
s = io.open(p, encoding="utf-8").read()
start = s.index("## Allure Behaviors 层级规范")
end = s.index("## 失败分类")
new = """## Allure 层级与用例结构规范

- `@allure.feature("模块中文名")`：模块名（如 `移动端首页`）。
- `@allure.story("L{N}-{页面/功能}元素")`：Layer + 页面/功能元素（如 `L1-页面结构元素`、`L2-交互行为元素`、`L3-异常与权限`）。
- 按 Layer 建类：`class TestL{N}{PageName}{Category}:`，类 docstring 为 `\"\"\"Layer {N}: §X.X.X 描述\"\"\"`。
- `@allure.title("L{N}-{NNN}: 用例中文标题")`；参数化用例用 `allure.dynamic.title` 带实际值。
- `@allure.severity(allure.severity_level.CRITICAL|NORMAL)`：P0=CRITICAL，P1/P2=NORMAL。
- pytest 标记：登录态用 `@pytest.mark.login_required` / `@pytest.mark.no_login`；执行策略用 `@pytest.mark.smoke` / `regression` / `full`。
- 每个测试 docstring 至少含：`PRD引用`、`覆盖层级`、`前置条件`、`测试步骤`（编号列表）、`预期结果`。
- 步骤与截图：`with allure.step("导航到目标页面"):` / `with allure.step("执行操作"):` / `with allure.step("截图记录"):`，截图放在对应步骤内；步骤名称来自 cases.md 的 `步骤` / `截图点`。

## Allure 截图步骤规范

- 每条用例的步骤按 cases.md 的 `步骤` 列书写；截图放在对应 `截图点` 的步骤内，不要用固定「用例结束态」替代全部步骤。
- 首页加载等公共动作不是每条用例都放，按 cases.md 截图点放置。
- 统一截图 helper 只作全页截图备选（`conftest.allure_screenshot`）；常规步骤截图用 `page.screenshot()` 直接 attach。
- 异常 / 负向用例截图必须贴近异常提示或失败状态；预期提示未出现时，仍要在失败前截图当前态并让用例失败，不要用普通首屏截图伪装异常覆盖。
- 上传异常类用例优先走真实可见上传按钮 + `expect_file_chooser()`，不要直接 `set_input_files()` 到隐藏 input，避免绕过业务组件的前端校验 / toast 链路。

"""
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("SKILL Allure 模板规范已写入")
