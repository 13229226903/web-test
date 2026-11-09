# Shared Contract（角色与主控共享）

> 本文件只放所有角色都要遵守的共享约束；主控专属规则（任务声明 / 状态机 / Gate / 上下文控制）见 `artifacts/runtime/orchestrator.md`。

## 共享红线

- 不删断言、不弱化断言、不把 expected 改成空 / `0` / `-` 来让测试通过。
- selector 优先 ID、role、稳定属性、文本；禁用 hash class、`:nth-child`、位置 XPath。
- 按钮交互必须引用 `page_map.states.<state>.buttons.<button_id>`。
- 不把需求实现错误记为 `skipped`；`skipped` 仅用于环境、数据、权限、授权或不可逆风险。
- 不执行未授权的删除、清空、注销、覆盖业务数据、对外通知、影响真实用户或不可逆提交；项目通过 `PROJECT.md` 明确授权的非生产环境积分消耗、生成 / 处理、模拟购买 / 订阅除外。
- 生成 / 购买 / 订阅 / credits 探索遵守项目账号和环境规则；项目明确授权时默认直接执行，并记录实际环境、账号、credits 变化、成功提交任务的 taskId（如有）及是否模拟支付。
- 上传素材只能使用 `test_images/` 现有文件。
- `seo-new-pages` 仅在用户明确要求 SEO 新页检测时使用。
- MCP 声明不跨会话继承：历史 artifact 只能证明当时的记录，不能证明当前会话已暴露对应 MCP 工具。任务要求 `playwright_mcp_only` 时，必须先在当前会话做最小 preflight；未通过则记录 `playwright_mcp_unavailable` 并停止。禁止静默降级为本地 Playwright、CDP 或 CUA；若用户明确授权替代驱动，必须在 `state.md` / progress 中如实改写并记录实际 driver。
- Playwright MCP 必须后台静默运行：不得调用 `bringToFront()` / 激活窗口；如浏览器窗口可见，必须把 MCP 窗口移出用户可见区域后再操作。**Windows 上 CDP `Browser.setWindowBounds` 的负坐标/大坐标会被钳制回屏内、`windowState=minimized` 也会被后续 `goto`/真实点击/file chooser 还原；正确做法是先按 `--user-data-dir=<...>/mcp-profile` 筛出 MCP 自己的 Chrome 进程树，仅对其 HWND 调用 Win32 `SetWindowPos(..., SWP_NOACTIVATE|SWP_NOSIZE)` 移到屏幕外（如 `-32000,-32000`），严禁移动用户自己的浏览器窗口。** 交互优先用页面内 `evaluate` / DOM 事件 / `setInputFiles`（不激活窗口），其次 CDP `Input.dispatchMouseEvent`，最后才用真实 `locator.click` 并在操作后复查窗口仍在屏幕外；需要键盘事件时优先派发 `KeyboardEvent`。详见 `rule.md`「Playwright MCP 后台静默」。
- PC 端任务必须执行 viewport guard：`innerWidth >= 1280`、`navigator.userAgent` 非 Mobile/iPhone/Android、`hasTouch=false`，并把 viewport/UA/touch/DPR 写入 state 或 evidence。
- `browser_resize` 只改变 viewport，不改 context 的 UA / isMobile / hasTouch / DPR；不得仅凭宽高达到目标值判定为 PC。若 MCP 默认 context 是移动仿真，必须在当前 MCP 内新建 desktop context；不能新建时记录 `playwright_mcp_context_mismatch` blocker 并停止，不得静默按移动端继续测 PC 用例，也不得降级到本地 Playwright / CDP / CUA。


### handoff 定位稳定性契约（2026-10-21）

- `automation_handoff.yaml` 的每个 `actions[]` 可声明 `locator`：`primary` / `fallback` / `stability` / `reason`。
- 稳定性分级：`high`（role/data-testid/aria）、`medium`（稳定属性 + 作用域，需 fallback）、`low`（顺序/坐标/无属性结构，需 fallback + `risk_notes`）。
- 条件显隐必须写 `not_visible_when`（如 Filter 前四滤镜无 Strength），test-writing 必须将其写成正向断言，不得跳过。
- 契约可声明 `confidence` 与 `failure_routing`（symptom → suspect → action），失败时按路由回退，不得无限自修。
- `validate_automation_handoff.py` 输出 warning（非阻塞）；`--strict` 时 warning 视为失败。review 阶段低/中稳定性 warning 未处理记为 Blocking。
## 探索交接与失效规则

- 探索阶段固定产出 `sync.md`、`exploration_report.md`、`evidence/automation_handoff.yaml`；前者是完整事实，第二个是人审摘要，第三个是自动化实现契约。
- `exploration_report.md` 必须按 `artifacts/runtime/templates/exploration_report.md` 输出，至少包含：已执行用例（按用例名，含 covered / bug_candidate）、Bug Candidate 明细（对应 AC / 用例名、步骤、实际、期望、证据截图）、未执行用例（按用例名，区分 gap / skipped）。
- Bug 证据截图必须插入报告，并放在默认折叠的 HTML `<details><summary>...</summary><img src="shots/...">...</details>` 中；禁止使用会被拆出折叠块的 Markdown 图片语法，`<details>` 内不要空行。
- `sync.md`、`page_map`、`cases.md` 任一发生版本、范围、账号、入口或 expected 变化，自动化 handoff 立即失效，必须回到 `ready_for_case_design` 并重新校验。
- 新增 / 变更任务的 test-writing 只能消费 `automation_handoff.status=implementation_ready` 的交接包；缺少 `ready_when`、reset、特殊 driver、事件采集边界或证据时不得自行补全。无变化的 stable regression 直接复用 confirmed registry 资产。
- 同一根因连续两次代码自修失败，必须退回上游角色；代码阶段不承担第二次探索。
- 代码调试不默认使用 MCP；只有故障分类为 `page_behavior_unknown` 时，才回退 page-map-sync 并重新使用 MCP 复核页面事实。

## 回归结果语义（2026-11-04）

- 回归结果必须按尝试级事实记录，并区分为 `clean_pass` / `retry_pass` / `quarantined` / `xfail` / `skipped` / `failed` / `broken`。
- `clean_pass`：首次 call attempt 通过；发布门禁可计入通过。
- `retry_pass`：早先 attempt 失败、后续 attempt 通过；必须保留首次失败证据，不得冒充 clean pass。
- `quarantined`：已登记的活跃隔离项；必须可见、必须排除在发布通过数之外，禁止删结果或计为通过。
- `xfail`：已知产品缺陷或预期失败，必须与 quarantine 分开统计。
- 汇总报告以 `reports/regression-<label>/<run_id>/regression_summary.json` 为机器可读门禁来源；Allure 只承担步骤、截图、附件和明细展示。
- 发布 / 归档门禁以 `regression_summary.gate.status` 为准：`!= passed` 时不得标记 completed、不得报「回归完成」、不得归档。
- 归档证据必须同时给出 `clean_pass_rate` / `retry_pass` / `quarantined`；三者缺一视为门禁证据不合规。
- 两条回归路径都必须产出汇总：`scripts/regression_runner.py`（registry）与 `scripts/run_full_regression.py`（-m regression）。
- quarantine registry 固定为 `artifacts/regression_quarantine.yaml`，至少记录 `case_id / reason / owner / opened_at / expires_at / evidence`。
- 禁止通过提高 retries / timeout 让结果变绿；重试只用于区分 first-run flaky 和真实修复。

### 失败分流与 flaky 治理（2026-11-05）

- 跨轮分析：`python scripts/flaky_report.py` 读取 `reports/attempts/*.jsonl`，按用例跨轮判定
  `stable_pass / stable_fail / flaky / new_fail / fixed / insufficient`。
- 需要处置的用例（flaky / new_fail / stable_fail 且未活跃隔离）会进入报告的 `needs_action`；
  必须按下方四类归因，不得只重跑。
- 失败分类（与 `orchestrator.md` 一致）：`test_code` / `runtime_environment` / `page_behavior_unknown` /
  `product_bug` / `flaky`（隔离并追根因）。
- 隔离登记：`python scripts/quarantine.py add <case_id> --reason --owner --evidence`
  必须带 owner / reason / evidence / 到期日；`release` 只置状态不删记录；
  `audit` 会标出过期项与连续多轮未修项。
- 隔离≠通过：`quarantined` 不计入 clean_pass / retry_pass，也不计入 release gate 通过数。
- 禁止：调大 retries / timeout 当治理手段；静默删除或永久 skip flaky 用例。

### case_id 解析优先级（2026-11-05）

- 优先级：recorder 的 `@allure.label("case_id")` / `allure.label("case_id", ...)` 标记 > Allure 结果 JSON 的 `case_id` 标签（覆盖 `allure.dynamic.label`）> 严格标题提取 > 可见的 `MISSING_CASE_ID` 债务。
- 标题提取只接受白名单格式：全局前缀（`TC-*` / `PC-HOME-*` / `P-AB-*` / `P-MX-*` 等）原样使用；短层级 ID（`L2-001`）必须加文件命名空间（如 `MH-L2-001`），因为短 ID 在多个脚本间重复。
- 无法识别时保留 `MISSING_CASE_ID`，禁止猜测。`regression_summary.json` 的每条用例记录 `case_id_source`，便于审计 ID 来源。

## Artifact 接力

- 角色之间只通过版本化 artifact 传递上下文；历史版本不覆盖、不删除，新产物用下一版本号。
- 归档确认后，允许按 orchestrator 的 archive-cleanup 规则清理未被引用的截图、snapshot、临时下载等中间产物；被引用证据与版本化正式 artifact 仍不得删除。
- 产物路径 `artifacts/<task_id>/...`；长输出先落盘，对话只留不超过 50 行的摘要和路径。
- 上一个 artifact 未达 `completed` / `confirmed` 不得接力；`pending_review` 必停等待用户。
- 同一 artifact 单写者；其他角色只读或创建新版本文件，不得并发修改。
- review / visual-review 只读，结论以 verdict / review note 写回独立文件。
- pytest / Allure 报告按用例矩阵输出：测试标题、参数化 id、labels 至少带 `case_id`。

## Progress 与 Journal

- 每次 append：`[YYYY-MM-DD HH:MM:SS] <actor> <event>`；至少记录 start、route/step、wrote artifact、gate、done/blocked。
- journal 叙事层：`scripts/journal.py log --actor <actor> --action <action> --target <target> --why "<reason>"`，只增不改；任务起手写 `artifacts/.current_task` 指针，终态清除。

## 知识沉淀规则

- 沉淀对象：本项目**反复出现、可复用、能帮后续任务避开坑直接走正确路径**的技术经验；一次性探索产物、纯业务事实、已过时经验、未复现的一次性观察均不沉淀。
- 沉淀条件（同时满足）：
  1. 反复出现：同一坑出现 ≥2 次；或仅 1 次但高成本（长时间排查 / 大量返工）。
  2. 可复用：后续新任务大概率还会遇到。
  3. 避坑导向：给出正确路径 / 规避方式，而非纯事实描述。
  4. 有证据：有 stable_regression 资产或实际运行结果背书；无则标注「待验证」。
- 沉淀落点：跨页面通用 → `rule.md`；项目事实（账号/素材/环境）→ `PROJECT.md`；页面专属 → 对应 `page_map/<模块>/<页面>.yaml` 的 `notes`；角色执行规则 → 对应 `skills/<role>/SKILL.md`；数据 → `data/*.yaml`。
- 触发时机：**归档前**。踩坑角色收集候选沉淀项，由 orchestrator 在 regression-archive gate 前汇总并向用户询问「是否需要沉淀」；用户确认后才写落点。
- 写入要求：标注来源（task_id / 验证方式 / 日期）；与 `regression_registry.md` 冲突时以 registry 为准，旧经验降级为「待验证」，不得当默认正确路径。

## 项目级约束指针

- Base URL、验证码、账号、素材白名单、DEBUG 开关文案等固定值不在此重复固化；全局账号 / 验证码 / 素材 / DEBUG 以 `PROJECT.md` 为准，通用编码与技术规则以 `rule.md` 为准。
- 账号态由探索结果（confirmed `sync.md` / `cases.md`）决定并写入任务级 `data/*.yaml`，探索与脚本阶段都据此取值，`conftest.py` 默认值仅兜底，不作为选账号依据。
- 任务级覆盖以对应任务的 `state.md`、`data/*.yaml` 和已确认 artifact 为准。

## 业务知识库运行契约

- 知识库目录为 `knowledge/`；索引为 `knowledge/index.yaml`，正文按 `shared.yaml` 与 `modules/<module>.yaml` 拆分，禁止把所有项目逻辑合并成单一总文档。
- 知识库是业务经验检索层，不替代 `rule.md`、`PROJECT.md`、`page_map/`、`sync.md`、`cases.md`；每条知识必须通过 `source_refs` 指向权威来源。
- 业务任务初始化必须做窄范围前置检索：先查索引，再读取 Top-K 命中切片；禁止全量加载知识库。
- 初始化最多 2 个 Query、每个最多召回 5 条；运行时单次最多 4 条；异常兜底单次最多 3 条；同主题无新证据不得重复检索。
- 每次检索必须记录 `hit_exact` / `hit_related` / `no_hit` / `conflict` 之一；无命中不是失败，但高风险主题必须转为现场验证清单。
- `active` 可作为候选依据；`needs_verification` 不得直接转为测试断言；`conflict`、`superseded`、`retired`、`ui_residue` 不得作为默认入口或预期。
- 角色发现的可复用经验先记录为当前任务 `knowledge_candidate`，归档前由 orchestrator 汇总、去重并向用户确认；未经确认不得写入 `active`。
- 知识库禁止保存密码、验证码、Cookie、Token、API key 等敏感值。
- 正式知识按业务模块归档，不按 task_id 建长期文件；task_id 只保留在候选、source_refs、evidence 和验证记录中。跨模块规则进 shared，模块规则进 `knowledge/modules/<module>.yaml`，页面当前事实进 page_map notes。





