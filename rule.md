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

## 画布类页面的状态持久化与会话级复用（有稳定资产背书）

- **画布编辑会持久化到 `pid`**：旧画布（`/create/edit?pid=...`）的图层增删 / 属性修改会写回同一个 pid，
  上一条用例的改动会带进下一条。复用画布时不要假设“重新打开 URL = 干净初始态”。
  - 用例执行顺序固定：结构 / 属性只读组在前，新增图层组在后；会改变图层尺寸的效果（如 Reflection 倒影）排在所属组最后。
  - 会互相污染的属性组（Opacity / Adjust / Shadow / Outline / Filter / Blend）在每条用例开始前统一调 reset helper 复位到默认值。
- **模板入口有频率限制**：连续走 `/template` 首卡上传约 17 次后会触发人机校验 / 上传不跳转（原始探索脚本同样失败）。
  → 不要逐条用例走上传入口；改 session 级前置只上传 / 建任务 1 次并记录画布 URL，其余用例新开 page 打开同一 URL（不重新上传）。
- **同一 pid 复用画布时，多层同文案/同色图层会完全重叠**：画布截图看不出层数，单层参数（Opacity/Space 等）改动在合成结果里几乎不可见
  （实测差异可低至 0.0001）。需要层数的用例必须用**图层列表面板计数**（如旧画布 Left Layer 面板：`layer-choosed` / `layer-unchoosed` 行）判定，不能只看画布；
  需要像素断言的用例应在操作前**清掉历史图层**（用户授权时可删）或给新图层换区别色，否则像素断言失去鉴别力。
  来源：`2026-09-11_old_canvas_text_panel_exploration`，13/13 通过。
- **面板内多个同类控件（滑杆/色块）必须按"label 下方最近的控件"定位**：同一分区里滑杆按行排列（如 Scope/Opacity/Distance/Angle），
  若取"分区内第一个 `input[type=range]`"，改 Distance 会实际打到 Scope；`querySelector` 也要限定在**该 label 所在行/最近容器**内，而不是整个分区。
  来源：同上（旧画布文字属性面板 Reflection 分区实测现象：Scope 被改、Distance 不变）。
- **同一页面可能挂载多套隐藏复用 section**：定位面板 / 分组时只认可见节点（`is_visible()` 过滤或 `:visible`），
  命中隐藏节点会导致改值无效、前后对比 diff=0。
- 来源：`2026-09-10_old_canvas_insert_panel_exploration`，2026-09-11 复跑 24/24 通过（改造后 24 次上传 → 1 次，42min → 9.5min）。

## 脚本复用与仓库资源路径（有稳定资产背书）

- **脚本被复制到别处运行时，仓库资源必须逐级上溯，不要用 `parents[N]` 写死层级**：
  `tests/` 下 `parents[1]` 是仓库根，但复制到 `archive/<模块>/` 后 `parents[1]` 变成 `archive/`，
  素材会被解析成 `archive/test_images/...` → `FileNotFoundError`（实测 7 个归档副本整轮回归误报失败）。
  - 统一写法：逐级上溯，取具备 `test_images/`、`data/`、`page_map/` 的目录作为仓库根（`_repo_root()`）。
  - 该坑同时覆盖 `test_images/` 素材、`data/*.yaml`、`page_map/*.yaml`——三者都要按仓库根解析。
- **跨 `tests/` 与 `archive/` 共用的公共 helper 放仓库根**：靠 root `conftest.py` 让仓库根进入 `sys.path`；
  不要在 `archive/<模块>/` 放同名副本（多份副本必然漂移，改一处漏一处）。
- **禁止在 `archive/` 下新增 `conftest.py`**：同名模块会遮蔽 root `conftest.py`，
  归档用例 `from conftest import allure_screenshot` 直接 ImportError（实测已回退该做法）。
- 来源：`2026-09-14_stable_regression_all_archived`；验证：7 个归档副本素材 / 数据路径整改 + helper 上收仓库根后
  `pytest --collect-only` = 106 tests / 0 error（2026-09-15）。

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
- **提交 / 确认控件未必是 `button`**：旧画布的绘制态 Apply / Cancel 实际是 `div`。定位交互元素时不要写死标签，
  用「可见文本 + 可见性过滤」拿到中心坐标后 `page.mouse.click(x, y)`；退出判据用「该控件消失」。来源：2026-09-10 旧画布任务，24/24 通过。
- **色板 / 调色板类控件通常无 aria 与文本**：按容器内元素的 computed `backgroundColor` 精确匹配目标色，
  再点其 `div.cursor-pointer` 祖先；直接点色块可能弹出调色板 overlay，需 Escape 关闭后再继续。来源：同上。


## 视觉审查模型

- 视觉审查的模型 / API 解析以 `skills/ui-test-visual-review/SKILL.md` 与 `helpers/review_api_config.py` 为准，不在此固化。

## 待验证（无当前稳定资产背书）

以下经验来自更早的探索或未登记脚本，当前 `regression_registry.md` 的稳定资产均未使用；遇到相关场景前先实测，不要默认套用：

- `force=True` 触发 Vue 文件选择器（当前登记资产用坐标点击 / `dispatchEvent`）。
- `networkidle` 作为等待主路径（当前登记资产用 `domcontentloaded` + `wait_for_timeout`）。
- `session_page` 会话级登录复用（当前登记资产用自定义 fixture / 自建登录，或匿名可用）。
- `pytest.xfail("独立脚本已验证通过")` 绕过 pytest 环境限制（当前登记资产未使用）。
