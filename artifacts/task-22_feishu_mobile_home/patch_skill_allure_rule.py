import io
p = r"skills\ui-test-test-writing\SKILL.md"
s = io.open(p, encoding="utf-8").read()
old = """## Allure 截图步骤规范

- 任何进入最终 Allure 报告的截图，都必须用显式步骤包裹：`with allure.step("操作边界/结果态"):` 再 attach；步骤名描述“发生了什么”，附件名描述“看到什么”，不要只留裸截图。
- 统一截图 helper 必须自己创建 Allure step；调用方不再手动重复 attach（本项目 `conftest.allure_screenshot` 已实现）。
- 异常 / 负向用例截图必须贴近异常提示或失败状态；预期提示未出现时，仍要在失败前截图当前态并让用例失败，不要用普通首屏截图伪装异常覆盖。
- 上传异常类用例优先走真实可见上传按钮 + `expect_file_chooser()`，不要直接 `set_input_files()` 到隐藏 input，避免绕过业务组件的前端校验 / toast 链路。"""
new = """## Allure Behaviors 层级规范（与 cases.md 分层对齐）

- `@allure.epic` = 功能名（如 `移动端首页`、`人像检测入口页`）。
- `@allure.feature` = Layer 分层名：`L1 页面元素与结构` / `L2 交互与状态迁移` / `L3 异常与权限` / `L4 PRD AC 逐条映射` / `L5 数据边界与等价类` / `L6 核心 Happy Path / E2E`。
- `@allure.title` = `<case_id> [<P0|P1|P2>] <短标题>`；参数化用例用 `allure.dynamic.title` 把实际参数值带进标题。
- 不用 `@allure.story` 作为主层级；`labels` 至少带 `case_id`。
- 每条用例至少 1 张截图：结束态直接 `allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)`；不要每条用例都重复放首页加载截图。

## Allure 截图步骤规范

- 只有需要表达「操作边界/结果态」的明确步骤时，才用 `allure.step` 包裹并 attach；普通结束态截图按上面层级规范直接 attach，不额外包 step。
- 统一截图 helper 应保持行为简单：`conftest.allure_screenshot` 作为全页截图备选；常规用例结束态用 `page.screenshot()` 直接 attach，避免每条用例重复调用全页 helper。
- 异常 / 负向用例截图必须贴近异常提示或失败状态；预期提示未出现时，仍要在失败前截图当前态并让用例失败，不要用普通首屏截图伪装异常覆盖。
- 上传异常类用例优先走真实可见上传按钮 + `expect_file_chooser()`，不要直接 `set_input_files()` 到隐藏 input，避免绕过业务组件的前端校验 / toast 链路。"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("test-writing SKILL Allure 规范已补充/对齐")
