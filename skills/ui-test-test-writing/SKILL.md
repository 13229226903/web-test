---
name: ui-test-test-writing
description: 根据 confirmed cases 与 versioned page_map 编写自动化脚本，执行 compliance、collect-only、自跑与最多三轮技术性自修，输出 impl.md。需要写自动化脚本时使用。
---

# test-writing

> 共享契约（通用红线 / Artifact 接力 / progress / 项目约束）见 `artifacts/runtime/common.md`。
> 编码与技术避坑规则（selector / 等待 / Vue 交互 / 状态持久化 / 截图粒度）另见 `rule.md`，写代码前定向检索。

## 职责
1. 读 confirmed cases + page_map + 项目约定。
2. 写测试代码（`tests/`）与测试数据（`data/*.yaml`）。
3. 轻量自检（compliance）→ collect-only → 自跑 → 自修（最多 3 轮）。
4. 收敛后写 impl.md；全过标记 regression_candidate；review / 归档由后续 gate 完成。

## 触发
- 用户主动写自动化；orchestrator 在 cases.md confirmed 后派发。

## 入口前置检查（任一不满足则拒绝/退回，不写代码）
1. cases.md 存在且 `status=confirmed`，且 `phase != requirement_draft`。
2. 完整流程中 sync.md 也必须 confirmed；selector 漂移局部重探需有授权豁免记录。
3. page_map 存在且 cases.md 的 page_ref 都能解析；按钮用例必须定位到 `states.<state>.buttons.<button_id>`。
4. 稳定回归优先复用现成资产，仅漂移 / 差异 / 需求变更才回退探索或设计。
5. 测试环境可访问（见 PROJECT.md base_url / 登录约定）。
6. 每条用例有可执行步骤清单（进入、操作、等待、断言、截图点）。
7. AI 审查用例有可执行视觉判断目标，不能只写“截图正常”。
8. Layer / 执行策略 / 用例 ID / L5 边界值可核对；sync 无未处理阻塞 bug_candidates。

## 新功能阻塞缺陷处理
- 只消费 `final_after_sync` 且 confirmed 的 cases；若仍是 draft / page_ref TBD / 有未处理阻塞 bug，写 `impl.md status=blocked` 退回。
- 用户明确要求为已确认 bug 写修复后回归用例时，保留需求期望为断言，不弱化。

## 实现风格
1. 优先复用既有数据驱动 / PO 层，不为单场景硬编码一次性 selector。
2. selector 走稳定定位（ID / role / 稳定属性 / 文本，禁用 hash class / :nth-child / 位置索引）——共享红线。
3. 按钮从 cases 指向的 `states.*.buttons.*.selector` 取，按 trigger / visible / enabled 执行前置；断言覆盖 action_result / assertions_hint。
4. 上传素材只用 cases 指定的 `test_images/` 文件，不生成 / 下载 / 换图。
5. 测试**用例文件**统一 `tests/`；跨 `tests/` 与 `archive/` 复用的公共 helper / 驱动模块放**仓库根**，不要在归档目录留副本（详见 `rule.md`）。
6. 断言：有意义的字段都断言；expected 不为空 / `0` / `-`；视觉 fail 必须传导失败。
7. 测试数据外置 `data/*.yaml`；账号态按 confirmed `cases.md` / `sync.md` 写入，`conftest.py` 默认仅兜底。
8. 去重 / 多值覆盖：一条用例覆盖多个等价值时用单条内部循环，不用 `parametrize` 展开，保证 Allure 报告用例总数 = cases.md `case_count`（仅当 cases.md 明确要求参数化时才用）。

## 自跑流程
1. 写代码 / data → 2. compliance 自检（无删断言 / 弱化 / 空 expected / 通配 selector）→ 3. `collect-only` 无 error/warning → 4. headless 自跑 → 5. 全过写 impl.md completed；review 后追加 report-output 生成并打开 allure matrix 报告。
- 失败 round+1，最多 3 轮，超限 `blocked_after_3_retries`。

## impl.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`status(completed|blocked|blocked_after_3_retries|likely_bug)`、`inputs`、`outputs(test_file,data_file,collect_only,self_run)`、`regression_candidate(eligible,reason,suggested_tests,suggested_archive,registry_key)`、`next_agent`。
- 正文：实现摘要、每轮自修日志、命令、结果、失败归因、报告路径与截图覆盖说明。

## Vue 交互与文件选择器

- **点击 / 填充类 Vue 组件**：优先坐标点击 `page.mouse.click(x, y)`，再回退 `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))`。
- **文件上传类按钮**：优先真实按钮 + `page.expect_file_chooser()` 选图；`input[type=file].set_input_files()` 只作回退且会丢失 Vue 工具上下文。
- **登录提交按钮**：用 `dispatchEvent`。
- **页面跳转类按钮**：不能套用上传 helper，用 `dispatchEvent` + 等导航 URL 变化。
- pytest-playwright 的 `browser_context_args` 必须设 `viewport` + `locale: "en-US"`，否则 Vue 文件选择器无法被拦截（见 `conftest.py`）。
- 滑块 / 数值型 Vue 控件：改值后用 `dispatchEvent(new Event('input'/'change', {bubbles: true}))` 触发更新。

> 待验证（无当前 stable_regression 资产背书，不要默认套用）：
> - `btn.click(force=True)` 触发 Vue 文件选择器；
> - `pytest.xfail("独立脚本已验证通过")` + `scripts/verify_<模块名>.py` 绕过 pytest 环境限制。

## 输出格式

- `@allure.feature("模块中文名")`：模块名（如 `移动端首页`）。
- `@allure.story("L{N}-{页面/功能}元素")`：Layer + 页面/功能元素（如 `L1-页面结构元素`、`L2-交互行为元素`、`L3-异常与权限`）。
- 按 Layer 建类：`class TestL{N}{PageName}{Category}:`，类 docstring 为 `"""Layer {N}: §X.X.X 描述"""`。
- `@allure.title("L{N}-{NNN}: 用例中文标题")`；参数化用例用 `allure.dynamic.title` 带实际值。
- `@allure.severity(allure.severity_level.CRITICAL|NORMAL)`：P0=CRITICAL，P1/P2=NORMAL。
- pytest 标记：登录态用 `@pytest.mark.login_required` / `@pytest.mark.no_login`；执行策略用 `@pytest.mark.smoke` / `regression` / `full`。
- 每个测试 docstring 至少含：`PRD引用`、`覆盖层级`、`前置条件`、`测试步骤`（编号列表）、`预期结果`。
- 步骤与截图：`with allure.step("导航到目标页面"):` / `with allure.step("执行操作"):` / `with allure.step("截图记录"):`，截图放在对应步骤内；步骤名称来自 cases.md 的 `步骤` / `截图点`。
- 每条用例的步骤按 cases.md 的 `步骤` 列书写；截图放在对应 `截图点` 的步骤内，不要用固定「用例结束态」替代全部步骤。
- 首页加载等公共动作不是每条用例都放，按 cases.md 截图点放置。
- 上传异常类用例优先走真实可见上传按钮 + `expect_file_chooser()`，不要直接 `set_input_files()` 到隐藏 input，避免绕过业务组件的前端校验 / toast 链路。

## 提交类用例任务记录（taskId / efMode / styleId）

- 生成 / 处理类用例（真实提交后端任务，如 Enhance 提交）在**成功提交后**必须抓取并记录该次任务的 `taskId`，并同时记录 `efMode` 或 `styleId`（存在则记，缺则不写不伪造）：
  - `taskId`（必记）：提交前注册 `page.on("console")`，用正则抓纯文本 `轮询结果\s+([A-Za-z0-9_\-]+)\s+Ng`；或解析 `handleSubmitTask result` 对象的 `data.taskId`（`msg.args[1].json_value()`）；或 `[aigc-task-poll]` 轮询对象 `taskIds[0]`。
  - `efMode`（legacy picEnhance 链路，如 Normal 2K = `240100021`）：`handleSubmitTask data` 文本 `efMode:\s*(\d+)` 或对应 args 对象。
  - `styleId`（ComfyUI / aiEnhance 链路，如 `pkweb_comfyui_enhance_natural`、`pkweb_realesrgan`、`pkweb_chain_comfyui_enhance_ultra`）：`[AIGC 提交][开始提交]` 文本 `styleId:\s*([^,}\s]+)`。
  - 链路差异：2K 非 Ultra legacy 链路会出现 `styleId: none` 但带 `efMode`；ComfyUI 链路有 `styleId` 无 `efMode`；两者都没有时记录 `resourceCode` 并标注“efMode 待后端核验”。
- 断言 `taskId` 非空；记录内容以 `allure.attach.file()` 或 JSON attachment 进 Allure 报告（字段：taskId / efMode / styleId），按需另落 json 便于对账。
- 每次提交前清空监听列表或使用独立 page，避免多任务 id 串扰；提交后异步等待用**轮询等 console 出现 taskId 或结果图层**，不得只固定 sleep。
- 任务 id 规则与探索阶段一致，来源见 page-map-sync SKILL「提交任务证据记录规则」与 `explore_18_taskid_console.json` 实测样例。

## 截图时机与粒度（有稳定资产背书）

- 跳转、切语言、打开新标签页后不要立刻截图；先等渲染完成，否则可能得到纯白截图。
- 通用做法：截图前等待 `networkidle`（建议 2s 超时，超时可接受）并再等 500ms；必要时再滚动到目标区域。
- **截图粒度是“状态”，不是“断言条数”**：
  - 一个步骤内如果有多条断言但 UI 状态未变化，只截一张图，放在整组断言之后。
  - 不要在同一步骤内为每条 `assert` / `expect` 各截一张图。
  - 不要同时保留“步骤截图”和“用例末尾汇总截图”来记录同一个状态。
- **必须截图的状态**：
  - 初始 / 默认态
  - 用户操作后的新状态（上传、切 tab、打开弹层、选中、删除、下载等）
  - 异步任务完成后的结果态
  - 视觉对比类步骤的前后状态（如 Refine 的 Eraser / Keep）
- **可省略截图的情况**：
  - 多条断言只是检查同一静止 UI 的不同字段
  - 等价路径产生完全相同的视觉状态；可只保留一个代表状态截图
  - 纯导航 / 纯等待步骤，且没有可断言的新状态
- **Allure 附件**：优先使用 `allure.attach.file()` 附加截图文件；不要只在 step 内用 `allure.attach(bytes)`，否则报告生成后可能出现附件展不开的问题。
- **证据截图默认整页（viewport 全幅），不要默认裁切**：附件需要包含左侧面板 / 画布 / 右侧属性面板 / 顶部栏等上下文；
  只有需要聚焦某个视觉效果的“特写”才显式裁切（如画布区域）。纯做像素差异比对的裁切图**不要**附加进 Allure 证据。
  来源：`2026-09-10_old_canvas_insert_panel_exploration`，用户反馈“只截到图片没截整页”后修订，2026-09-11 复跑 24/24 通过。
- 空态 / 初始态 / 未操作前截图必须在触发状态变化的操作之前截取；状态变化后再补一张变化后截图，不得用变化后的截图冒充空态。
- 异常 / 负向用例截图必须贴近异常提示或失败状态；预期提示未出现时，仍要在失败前截图当前态并让用例失败，不要用普通首屏截图伪装异常覆盖。
- 来源：`2026-09-07_pokecut_pc_home_dev_interactions`，2026-09-08 复跑 17/17 通过，空白截图 0；`2026-09-08_pokecut_pc_batch_dev_interactions` 补充 step 附件、状态级截图与等价状态去重规则。

## 失败分类
| 现象 | 怀疑 | 行动 |
|---|---|---|
| 点击 / 填充 30s timeout | selector 漂移 | 对比失败截图 / DOM 与 page_map → 报 page-map-sync |
| DOM 有值但断言区空 / `-` | 后端字段 bug | `likely_bug` 退出等人 |
| 表单校验失败 | 业务校验 | 改 data 为合法格式 |
| 按钮点击不切换 | UI 改版 / headless 未生效 | hover + click 或 URL 直达 |
| 下拉选不上 | option 文本变 | 找新文本改 data |
| 视觉 fail 但 Allure 通过 | 注入 / 传导缺失 | 修审查注入 / 断言传导后重跑 |
| 只有截图无结果断言 | 用例实现不完整 | 补真实结果断言或 AI 审查 |
| collect-only 出现 `[None]` / `[最小值]` | 参数 ID 缺实际值 | 回退用例设计，不真跑 |
| PRD 边界与页面实际不一致 | 产品缺陷 / PRD 差异 | 保留断言，标 `likely_bug` / `PRD_actual_mismatch` 请用户裁决 |

## 角色红线（共享红线见 common.md）
- 按钮交互不得脱离 `states.*.buttons` 自行重猜 selector；page_map 缺失退回 page-map-sync。
- 修地图 vs 修代码必须写明依据进 impl.md 自修日志；例外可改 cases.md 的 page_ref 引用，不改 page_map。
- 循环上限 3 轮，不突破。
- 不修改 sync / cases / review；不直接改 page_map。
- 真 bug → `likely_bug` 并保留完整断言（`xfail(strict=True)`），不改断言迁就。
- 视觉 fail 必须传导失败。
- collect-only 失败 / ID / Layer 不一致 / L5 参数无实际值不得真跑。
- 自修复只允许改 selector、等待、导航、数据格式、测试实现；不得为绿灯改 expected / 语义。
- Allure 中文标题 / 描述 / 步骤并含 Layer；参数化标题显示实际值。
- 不省略 progress.log。
- 统计埋点 / GA 事件（探索结论中的事件名与触发方式）不写入回归脚本；埋点验证只在探索 sync.md / evidence 层输出，除非用户显式要求写。

## progress
- start / step:wrote <file> / step:collect_only / step:round N / done:impl.md / gate:regression_archive_candidate

## 上下游
- 上游：orchestrator（cases confirmed）。
- 下游：全过 → null（orchestrator 派 review）；selector 漂移 → page-map-sync；真 bug / PRD 差异 / 超 3 轮 → null 等人。
