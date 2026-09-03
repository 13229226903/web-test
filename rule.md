# 编码规则与技术避坑

> 本文件只放「跨页面通用的编码与技术规则」，供所有角色写代码、探索页面前读取。
> - 项目级事实（base_url / 目录 / 登录 / 账号 / 素材 / DEBUG 环境顺序）：见 `PROJECT.md`
> - 页面专属元素与交互坑：写入对应 `page_map/<模块>/<页面>.yaml`，不在本文件堆叠
> - 角色专属执行规则：写入对应 `skills/<role>/SKILL.md`
> - 路由 / Gate / 归档：见 `artifacts/runtime/orchestrator.md`
> - 知识沉淀（哪些沉淀 / 不沉淀 / 何时询问）：见 `artifacts/runtime/common.md`「知识沉淀规则」
>
> 下面「通用经验」以 `artifacts/regression_registry.md` 当前 stable_regression 资产的实际用法为准；
> 未被当前资产背书的旧经验单独列在「待验证」，不得当作默认正确路径。

## Selector 优先级（从高到低）

1. **语义 ID / role**：`page.get_by_role("button", name="Save")`、`#firstName`
2. **稳定属性**：`[placeholder="..."]`、`[aria-label="..."]`、`[data-testid="..."]`、`[href*="/topics/"]`、`[data-tool-id="..."]`
3. **文本定位**：`page.get_by_text(...)`、`button:has-text("提交")`
4. **避免**：hash class（随构建变化的 `.css-1a2b3c`）、`:nth-child(n)`、xpath 位置索引

## 等待时机（有稳定资产背书）

- 主路径：`page.goto(..., wait_until="domcontentloaded")` 后，用 `page.wait_for_timeout(...)` 等 Vue/SPA 水合完成再操作。
- 断言用 Playwright `expect(...)`（自带自动重试），不要 `assert locator.is_visible()`。
- 浮层（下拉/菜单/弹窗）出现后再操作，必要时 `expect(locator).to_be_visible()` 卡一下。

## 组件行为（通用）

- 三点菜单 / hover 菜单：先 hover 行，再点触发图标，菜单才渲染。
- popconfirm / tooltip 经常没有 `role=dialog`，按文本或就近容器定位。

## 测试设计

- 所有字段都填（含非必填），所有有意义的字段都断言。
- `expected` 用有语义的值，不要用 `"0"` / `"-"` / 空字符串。
- 文本型断言用「包含子串」而非精确相等，避免格式漂移。
- 注释用中文。

## Vue 交互与文件选择器（有稳定资产背书）

- **点击 Vue 组件**：优先 `page.mouse.click(x, y)` 坐标点击，再回退 `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))`。
- **文件上传**：优先真实按钮 + `page.expect_file_chooser()` 选图；`input[type=file].set_input_files()` 只作回退，且会丢失 Vue 工具上下文。
- **context 配置**：必须设 `viewport` + `locale: "en-US"`，否则 Vue 文件选择器无法被拦截（`conftest.py` 已统一兜底）。
- 滑块 / 数值型 Vue 控件：改值后用 `dispatchEvent(new Event('input'/'change', {bubbles: true}))` 触发更新。

## 视觉审查模型

- 视觉审查的模型 / API 解析以 `skills/ui-test-visual-review/SKILL.md` 与 `helpers/review_api_config.py` 为准，不在此固化。

## 待验证（无当前稳定资产背书）

以下经验来自更早的探索或未登记脚本，当前 `regression_registry.md` 的稳定资产均未使用；遇到相关场景前先实测，不要默认套用：

- `force=True` 触发 Vue 文件选择器（当前登记资产用坐标点击 / `dispatchEvent`）。
- `networkidle` 作为等待主路径（当前登记资产用 `domcontentloaded` + `wait_for_timeout`）。
- `session_page` 会话级登录复用（当前登记资产用自定义 fixture / 自建登录，或匿名可用）。
- `pytest.xfail("独立脚本已验证通过")` 绕过 pytest 环境限制（当前登记资产未使用）。
