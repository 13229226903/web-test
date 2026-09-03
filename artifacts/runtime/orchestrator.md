# Runtime Orchestrator Card

职责不变：路由任务、维护状态机、加载并执行角色 skill、处理 Gate，不代替业务角色产业务 artifact。

## 启动

1. 读 `artifacts/runtime/common.md`。
2. 判定任务类型并创建/恢复 `artifacts/<task_id>/state.md`、`progress.log`、`shots/`、`artifacts/.current_task`。
3. 只加载当前阶段 `skills/<role>/SKILL.md`；不要预读全部角色。
4. 若为 Codex 且未使用隔离子代理，记录 `execution_mode: codex_single_context`，在同一上下文按角色顺序模拟。


## 任务输出产物契约

用户自然语言可以约束执行范围、环境和探索方式，但不得改变 runtime / role skill 规定的标准输出产物契约，除非用户明确要求改变产物格式或另存为补充文件。

- 标准产物名、目录、frontmatter schema、正文结构、Gate 和状态机均以 runtime / role skill 为准。
- `sync` gate artifact 固定为 `artifacts/<task_id>/sync.md`；不得因执行方式、临时说明或探索手段不同而改名。
- 补充材料可以另存为 evidence / appendix，但 `state.md` 的接力指针必须指向标准产物。
- 写产物前若仓库已有同类 artifact，应优先对齐同类历史格式；不确定时先查看同类历史产物，而不是自创结构。
- 执行前应在 `state.md` 固化关键字段，至少包含：`task_type`、`execution_mode`、`target_url`、`artifacts.sync`、`next_step`；如有特定探索驱动，再记录对应 driver 字段。

## 执行模式自动选择

主控判定 `task_type` 后，按以下优先级决定 `execution_mode` 并写入 `state.md`：

1. 用户明确要求隔离 / 审计 → `codex_subagent`
2. `task_type == single_agent` → `codex_single_context`
3. `task_type == stable_regression` → `codex_single_context`（selector 漂移 / 页面差异 / 需求变更的局部复探也留在主会话）
4. `task_type == new_feature_test` 或 `existing_feature_first_exploration` 且 `scope` 为全流程 → `codex_subagent`
5. 只读角色（`page-map-sync` / `review` / `visual-review`）即使整体为 M1，也优先用独立子代理派发 → `codex_subagent`
6. 紧耦合、连续交互的页面操作，或无法使用子代理 → `codex_single_context`（无法使用时在 `state.md` 记录原因）

同一次任务可混用：`state.md` 的 `execution_mode` 记录整体模式，各角色实际派发方式在 `progress.log` 单独记录。

## 探索驱动

- `page-map-sync` 的探索驱动固定为 Playwright MCP only，并在 `state.md` 记录：`exploration_driver: playwright_mcp_only`、`diagnostic_driver: none`。
- Playwright MCP 只作为页面观察与交互驱动层；MCP snapshot / screenshot / console 等输出是探索证据，不替代 `page_map`、`sync.md`、`progress.log` 或后续 pytest / Playwright 可复跑脚本。
- Chrome DevTools MCP 不作为默认诊断工具；如果仅凭 Playwright MCP 无法判定按钮无响应、接口异常、白屏、性能问题或 JS 根因，应在 `sync.md` 记录 `diagnostic_limit: playwright_mcp_only_no_devtools_trace`，并按 `bug_candidate` / `blocked` 处理，不扩大工具链。
- selector 规则不因 MCP 改变：仍优先 ID、role、稳定属性、文本，禁止 hash class、`:nth-child`、位置 XPath；不得把 Playwright MCP 临时 element ref 直接沉淀为测试 selector。

## 任务声明

```yaml
task_type: new_feature_test | existing_feature_first_exploration | stable_regression | single_agent
requirement_doc: <path>
entry_url: <url>
entry_path: <path>
scope: <coverage>
stop_at: sync_review | cases_review | regression_archive | final_report
exploration_driver: playwright_mcp_only
diagnostic_driver: none
forbidden: <forbidden stages/skills>
assets: <accounts/data/environment>
```

缺字段时采用合理默认值，并把假设写入 `state.md`。除下方 schema 外，`state.md` 还需记录 requirement_doc、target_url、entry_path、scope、stop_at、exploration_driver、diagnostic_driver、assumptions、artifacts、next_step、blockers。

也支持自然语言下达，主控会自动补齐 scope / stop_at / 账号态 / assets 等并写进 state.md 的 assumptions；只有 PRD 路径与入口 URL 缺失时才向用户确认。示例：

- 新功能全流程：把这份 PRD 走完整流程，PRD 在 `<path>`，入口 `<url>`，全流程到归档。
- 存量首次探索：`<url>` 这个功能已经上线了，帮我补页面地图、用例和脚本。
- 稳定回归：回归一下 homepage 已登记的脚本。
- 单角色：只更新 xxx 页面的地图 / 根据这份需求写用例 / 按 confirmed cases 写自动化 / 审查这次脚本改动 / AI 看一下这两张截图。

## 路由

| 任务类型 / 意图 | 路由 |
|---|---|
| 新功能 / 大改版 / 首次提测 + PRD | test-case-design(requirement_draft) → page-map-sync（按 requirement_draft 用例/AC 逐条对照实际页面执行探索，产出 requirement_actual_diffs）→ sync gate → test-case-design(final_after_sync) → cases gate → test-writing → review → test-writing(report-output) → regression-archive gate |
| 存量功能首次探索 / 补资产 | page-map-sync → sync gate → test-case-design(final_after_sync) → cases gate → test-writing → review → test-writing(report-output) → regression-archive gate |
| 稳定回归 | 优先执行 `artifacts/regression_registry.md` 登记脚本；selector 漂移 / 页面差异 / 需求变更才局部回退。执行完成后按下方「稳定回归报告输出」生成并打开 Allure 报告，同时在对话里打印简易回归报告 |
| 更新地图 / selector 失效 | page-map-sync |
| 设计用例 / 需求转用例 | test-case-design；新功能未提测显式 `phase=requirement_draft` |
| 写自动化 / 补脚本 | confirmed cases 后 test-writing |
| 审查 | review |
| AI 视觉审查 | visual-review |

新功能必须需求先行，不得直接从 page-map-sync 开始。新功能的 page-map-sync 是**用例驱动探索**：以 `requirement_draft` 的用例 / AC 为探索清单，逐条在实际页面执行 / 核对，需求预期与页面实际的差异记入 sync.md 的 `requirement_actual_diffs`（`covered` / `gap` / `bug_candidate`），不做脱离用例的全量盲扫。存量首次探索不走 requirement_draft，以页面现状补齐资产。稳定回归不做全量探索。

## 角色 skill 执行规则

- 一次只执行一个角色 skill 的一个 round。
- 每个角色 skill / 子任务只读取 common.md、对应角色 SKILL.md、当前 state.md、最近一次确认的阶段 artifact 和必要 handoff 包，不得默认读取整条历史对话。
- 角色 skill 输入自包含：task_id、task_type、role、entry_url、entry_path、scope、exploration_driver、diagnostic_driver、输入 artifact、输出 artifact、stop_at、forbidden、账号态和授权边界。
- 每次角色 skill 执行返回后先更新 state，再进入下一步。
- Codex 单上下文中，当前角色 artifact 未落盘、state/progress 未更新，不得进入下一角色。
- 角色 skill 不得嵌套执行；review 物理只读，由 orchestrator 落盘 review.md。

## 并发约束（当前环境 API 并发上限 = 1）

- M2 子代理必须串行：spawn 一个 -> wait_agent 完成 -> 再 spawn 下一个。
- 禁止同时 spawn 多个子代理；即使存在可并行的只读子任务，也按串行处理。
- 主控等待子代理期间不发起其他 API 调用，保证任意时刻只有 1 个 agent 在运行。

## state.md 最小 schema

```yaml
---
task_id: <id>
agent: orchestrator
status: in_progress | completed | blocked | failed
current_step: <role or waiting/gate step>
execution_mode: codex_subagent | codex_single_context
task_type: new_feature_test | existing_feature_first_exploration | stable_regression | single_agent
human_gates_pending: []
agent_call_count:
  page-map-sync: 0
  test-case-design: 0
  test-writing: 0
  review: 0
  visual-review: 0
created_at: <timestamp>
---
# 调度历史
# 终态原因
```

## 调用上限

- page-map-sync：2
- test-case-design：新功能 2（draft + final），其他 1
- test-writing：1（内部自修最多 3 轮）
- review：同一改动最多 3 轮，超限 `blocked_after_3_reviews`
- visual-review：同一视觉点最多 2 次，超限传导 `blocked`

超限写 `status=blocked` 与原因，等待用户。

## 探索结果摘要输出（新功能 / 存量首次探索的 page-map-sync 阶段）

探索阶段不跑 pytest、不产出 Allure 报告（Allure 是 test-writing 执行自动化用例后的产物）。探索结束时必须在对话里打印「探索结果摘要」，按用例 / AC 逐行展示：

```text
【探索结果摘要】<YYYY-MM-DD HH:MM>
功能: <feature 名>
模式: 新功能用例驱动探索 / 存量首次探索

✅ <case/AC> <标题> — covered
⚠️ <case/AC> <标题> — gap: <一句话需求 vs 页面差异>
❌ <case/AC> <标题> — bug_candidate: <一句话现象>
⏭ <case/AC> <标题> — skipped: <原因>

合计: <n> covered · <n> gap · <n> bug_candidate · <n> skipped
页面地图: <page_map 路径>
sync.md: <路径> (pending_review)

请审核 sync.md（覆盖矩阵 / 差异 / bug candidate）后确认进入下一阶段
```

行内要求：
- 每行一条用例 / AC（新功能）或关键覆盖点（存量首次探索），行首 ✅（covered）/ ⚠️（gap）/ ❌（bug_candidate）/ ⏭（skipped）。
- gap 与 bug_candidate 必须带一句话说明，不得只给数量。
- 阻塞主流程的 bug_candidate 要标注 `blocked`，提示先提 bug / 等用户决定。

## 简易测试报告输出（新功能 / 存量首次探索）

新功能 / 存量首次探索的 report-output 子步骤完成、打开 Allure 报告的同时，必须在对话里打印「简易测试报告」，按用例矩阵逐行展示：

```text
【测试报告】<YYYY-MM-DD HH:MM>
功能: <feature 名>

✅ <case_id> <用例标题>  [<Layer> <策略>]
⚠️ <case_id> <用例标题>  [<Layer>]  (skipped: <原因>)
❌ <case_id> <用例标题>  [<Layer>]  — <失败原因摘要>

合计: <passed>/<total> 通过 · <failed> 失败 · <skipped> 跳过 · 总耗时 <time>
状态: ✅ 全部通过（或 ❌ 有失败）

Allure 报告: http://localhost:8123/index.html
```

行内要求：
- 每行一条用例，行首 ✅（通过）/ ⚠️（跳过）/ ❌（失败）。
- 失败用例必须带一句话失败原因，不得只给数字。
- case_id / Layer / 策略与 `cases.md` 一致。

## 稳定回归报告输出

稳定回归跑完 registry 登记脚本后，orchestrator 必须：

1. `allure generate reports/allure-results -o reports/allure-report-regression --clean`（结果目录名用 `-regression`，与完整流程的 `-matrix` 区分）。
2. 启动本地 HTTP 服务器（如 `python -m http.server 8123 --directory reports/allure-report-regression`），并在浏览器打开 `http://localhost:8123/index.html`。
3. 在对话里打印「简易回归报告」，按 registry 任务逐行展示，格式如下：

```text
【回归测试报告】<YYYY-MM-DD HH:MM>

✅ <任务名>              <passed>/<total> · <耗时>
⚠️ <任务名>              <passed>/<total> · <耗时>  (<skipped> skipped)
❌ <任务名>              <passed>/<total> · <耗时>
   └ <失败用例名> — <失败原因摘要>

合计: <passed> 通过 / <failed> 失败 / <skipped> 跳过 · 总耗时 <总耗时>
状态: ✅ 全部通过（或 ❌ 有失败）

Allure 报告: http://localhost:8123/index.html
```

行内要求：
- 每行一个 registry 任务，行首状态符号用 ✅（全过）/ ⚠️（有跳过）/ ❌（有失败）。
- 失败任务必须逐条列出失败用例名和一句话失败原因，不得只给数字。
- 数据以 pytest 退出码 / 输出与 `regression_registry.md` 的 Last Passed 信息为准。

## 接力与 Gate

1. artifact `pending_review/failed/blocked` 不接力。
2. `sync.md pending_review`：在对话里打印「探索结果摘要」（格式见下方「探索结果摘要输出」节），通知用户审核覆盖矩阵、差异、bug candidate；停止。确认后改 confirmed；阻塞 bug 先提 bug / blocked，不进用例或脚本。
3. `cases.md pending_review`：通知用户审核用例矩阵；停止。确认后才能 test-writing。
4. `impl.md completed` 且自跑失败为 0：先 review；review fail 回 test-writing 或 blocked。视觉需求再 visual-review。
5. review / visual-review 通过后：先执行 `test-writing` 的 report-output 子步骤，生成并检查按用例矩阵输出的 `allure-results-matrix/` 与 `allure-report-matrix/`，确认 case_id / 参数化 id / title / epic / feature 与 `cases.md` 一致，且报告用例总数 = `cases.md` 的 `case_count`，且每条矩阵用例至少有 1 个截图步骤或已记录的例外说明后，启动本地 HTTP 服务器（如 `python -m http.server 8123 --directory reports/allure-report-matrix`），并在浏览器打开 `http://localhost:8123/index.html` 供用户查看（不得直接打开静态 HTML 文件），同时在对话里打印「简易测试报告」（格式见下方「简易测试报告输出」节）；用户确认后才进入 regression-archive gate。不得直接 completed。
6. 进入 regression-archive gate 时：orchestrator 汇总本次任务的候选沉淀项（同一坑出现 ≥2 次或 1 次但高成本），向用户询问「是否需要沉淀」；用户确认后按 `artifacts/runtime/common.md`「知识沉淀规则」写落点，并记录到 progress / journal。
7. 用户确认归档：先执行 archive-cleanup——生成删除清单，清理本次任务中未被 `sync.md` / `cases.md` / `impl.md` / `archive.md` / Allure 报告引用的截图、snapshot、临时下载等中间产物；被引用证据必须保留，清理结果写入独立 manifest / result 并记录 progress / journal。然后只做复制、registry 更新、archive.md；归档脚本复跑要另外生成 `allure-results-archive/` 与 `allure-report-archive/`。暂不归档：写 archive.md `skipped_by_user`，可 completed；未引用中间产物仍按本条清理。

## 上下文控制

- 每个命令只解决一个问题；找到目标、拿到关键状态或出现阻塞即停止。
- 不重复执行已有证据能回答的扫描。
- 截图写入 `artifacts/<task_id>/shots/`；单次输出超 50 行先落盘再汇报。
- 禁止在对话展开截图 base64、完整 HTML、accessibility tree、HAR、完整 pytest 输出。

## 异常

- 角色 skill 失败 / 超时：state 记 failed 和调度历史。
- 角色 skill 越界：拒绝接力并 blocked。
- Gate 中收到新 prompt：判断是继续等 gate 还是用户切换任务，并在 state 记录决策。
