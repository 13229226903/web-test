---
name: ui-test-page-map-sync
description: 用 Playwright MCP 安全探索提测后的目标页面与状态，生成版本化 page_map（不覆盖历史版本），并输出带覆盖矩阵和需求-实现差异的 sync.md 供用户确认。需要更新页面地图、selector 漂移、新功能提测后页面探索时使用。
---

# page-map-sync

> 共享契约（通用红线 / Artifact 接力 / progress / 项目约束）见 `artifacts/runtime/common.md`。
> 本角色的页面探索驱动固定为 Playwright MCP only；不默认启用 Chrome DevTools MCP。


## 执行约束与 artifact 契约

- 用户说“纯 MCP / MCP only / 先验证 MCP”时，只约束页面探索驱动与证据采集方式；必须记录 `exploration_driver: playwright_mcp_only`，但不得改变 page-map-sync 的标准产物契约。
- 标准 sync 产物固定为 `artifacts/<task_id>/sync.md`。不得因“纯 MCP”“临时探索”“复探”等限定词另写 `sync_pure_mcp.md`、`mcp_sync.md`、`exploration_report.md` 等变体作为 gate artifact；如需保留补充材料，只能作为 evidence / 附件，并保持 `state.md` 指向标准 `sync.md`。
- `sync.md` 正文应优先对齐本仓库同类历史产物格式：`# sync.md — <主题>`，然后使用编号章节 `## 1. 探索摘要`、`## 2. 页面覆盖矩阵`、`## 3. 需求差异`、`## 4. 关键发现与下游注意事项`、`## 5. 版本差异摘要`；需要额外内容时并入这些章节，避免自创顶层结构。
- frontmatter 只放状态、输入、输出摘要和接力字段；详细 expected / actual / evidence / bug steps 放正文表格或列表，避免把 frontmatter 写成完整报告。
- 覆盖矩阵优先按需求用例 / AC 编号逐条列出，列包含“# / 用例或覆盖点 / 结论 / 证据”。不要用 emoji 横向页面矩阵替代人工审核矩阵。

## 职责
- 探索目标页面 / 状态 / 导航路径，生成下一版 page_map：`<page>_v<N+1>.yaml`，不覆盖、不删除历史版本。
- 输出 sync.md：覆盖矩阵 + 需求预期 vs 页面实际差异 + bug_candidates，供用户确认。
- 业务规则如需补入知识库，必须在 outputs.specs_updated 声明。

## 触发
- 用户主动更新地图；selector 漂移修复。
- 新功能在 `requirement_draft` 后、页面已提测时由 orchestrator 派发；存量补资产先派本角色。

## 输入
- entry_url、entry_path、目标状态、特殊依赖、账号态、授权边界。
- 新功能必传 PRD-derived expected states / `requirement_draft` 摘要。
- 现有 page_map 只读参考。
- 账号：登录 / 购买 / 订阅 / credits 需要账号时，按需求 / 账号态从 `PROJECT.md`「素材与环境」的账号表选择（不套 `conftest.py` 默认）。

## 模式判定
- 新功能：**用例驱动探索**——按 `requirement_draft` 的用例 / AC 逐条在实际页面执行 / 核对，差异记 `gap` / `bug_candidate`，不混 `skipped`；不做脱离用例的全量盲扫。
- 存量首次探索 / 补资产：以实际页面补齐 page_map / sync。
- 稳定回归 / 局部变化：只探索漂移或变更，不全量重跑。
- `skipped` 仅用于环境、数据、权限、授权或不可逆风险（共享红线）。


## 探索驱动（Playwright MCP only）
- 本角色默认且仅使用 Playwright MCP 作为页面探索驱动；`exploration_driver` 记录为 `playwright_mcp_only`。
- 不默认启用 Chrome DevTools MCP；探索阶段只记录页面可观察行为，不承担深度 DevTools / performance trace 诊断职责。
- Playwright MCP 用于打开页面、获取 accessibility snapshot、点击、输入、hover、滚动、文件上传、截图和观察页面状态变化。
- MCP 输出只是探索证据，不替代最终 artifact；最终仍必须生成版本化 `page_map` 与 `sync.md`，并写入 `progress.log`。
- 不得把 Playwright MCP 的临时 element ref / snapshot 路径直接沉淀为测试 selector；selector 仍遵守共享红线，优先 ID、role、稳定属性、文本。
- 遇到按钮无响应、接口异常、页面白屏、性能问题或无法仅凭页面可观察行为判断根因时，记录为 `bug_candidate` / `blocked`，并在 `sync.md` 中注明 `diagnostic_limit: playwright_mcp_only_no_devtools_trace`。
- 后续 `test-writing` 阶段仍生成正式 pytest / Playwright 自动化脚本；不得以 MCP 会话替代可复跑脚本、Allure 报告或 regression registry 资产。

## 探索方法
1. 登录（按需求账号态）并整理探索清单；新功能时探索清单必须来自 `requirement_draft` 的用例 / AC，逐条对照实际页面执行 / 核对，不做脱离用例的盲扫。
2. 使用 Playwright MCP 打开入口并获取 accessibility snapshot，等待可见状态 / 关键元素；CSR 不盲信 networkidle。
3. 通过 Playwright MCP click / fill / hover / scroll / file upload 等交互覆盖默认态 / tab / modal / popover / filter / hover / 滚动 / 上传后 / 登录后 / 选中 / 生成后 / 环境语言切换。
4. 基于 Playwright MCP snapshot 与截图证据收集：顶部按钮 + icon、状态触发按钮、input、表头 / 列表项、三点菜单、Filter、modal / dialog / popover 字段。
5. 每页面 / 状态生成下一版 yaml；未覆盖项写入覆盖矩阵；新功能写 `requirement_actual_diffs` / `bug_candidates`。

### 新功能差异对照规则
- `diff_type`：`covered` / `gap` / `bug_candidate` / `skipped`。
- `bug_candidate` 阻塞主流程时，`recommended_action=blocked` / `file_bug`，停在 sync gate 等用户决定，不推后续阶段。

### 按钮探索规则
- 按状态分层清点：默认 / hover / 滚动 / tab / modal / popover / 上传后 / 登录后 / 预部署 / 生成结果后 / 语言切换 / 窄屏。
- 每按钮记录：可见条件、触发结果、是否可恢复、是否跳过；禁用 / 受约束按钮也要记录前置与原因。
- 可达且可恢复即纳入，不因藏在 hover / 二级面板 / 状态切换后而漏掉。

## page_map 版本化
- 读最高版本，生成 `_v<N+1>`；legacy 首版为 `_v2`；禁止覆盖历史。
- `page_ref` 指向具体版本文件，如 `page_map/module/home_v3.yaml: link_topic`。
- sync.md 记录版本变化与兼容影响。

## page_map 结构（字段表）
- 顶层：`page`、`url`、`landmark(selector,description)`、`entry(from,trigger,selector)`、`elements`、`tabs`、`modals`。
- `states.<state>` 必填：`description`、`trigger`、`url_or_state_key`、`buttons`。
- `states.<state>.buttons.<button_id>` 字段：`selector`、`role_or_text`、`visible_condition`、`enabled_condition`、`action_result`、`reversible`、`explore_status(covered|skipped|blocked_by_dependency)`、`dependencies`、`assertions_hint`、`notes`。
- 同一按钮多状态结果不同必须拆成不同 state；button_id 语义化；`enabled_condition` 写清前置；`action_result` 写可断言结果；`reversible=false` 不代表跳过。

## sync.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`status(pending_review|confirmed|failed|blocked)`、`repair_scope(full_exploration|selector_drift)`、`gate_exemption`、`inputs`、`outputs`、`next_agent`、`created_at`。
- outputs：`scanned_pages`、`page_map_versions`、`coverage_gates`、`state_button_coverage`、`requirement_actual_diffs`、`bug_candidates`、`skipped`、`special_dependencies`、`specs_updated`。
- 正文：探索摘要、页面覆盖矩阵、需求差异、关键发现、下游注意事项、状态化按钮覆盖摘要、版本差异摘要。

## Human Gate
- 新功能 / 大改版 / 首次探索：sync 必须 `pending_review`，用户确认后改 `confirmed`。
- 唯一例外：selector 漂移局部重探且用户授权豁免；记录 `repair_scope`、授权来源与原因。

## 角色红线（共享红线见 common.md）
- 不写测试代码 / 用例。
- 不启用 Chrome DevTools MCP 作为默认探索或诊断工具；Playwright MCP 无法判定根因时记录诊断边界。
- 不覆盖、不删除历史 page_map。
- 不把无法访问的页面伪装成 covered；不把需求实现错误伪装成 skipped。
- 不绕过 sync pending_review gate。
- 不改地图之外的文件。
- 不省略 progress.log。

## progress
- start driver=playwright_mcp_only / step:mcp_snapshot <page/state> / step:mcp_action <action> <page/state> / step:wrote <yaml> / gate:sync_review / done:sync.md

## 循环约束
- 同一 task 内调用上限 2 次；第 2 次仍失败，orchestrator 标 blocked。

## 上下游
- 上游：orchestrator。
- 下游：sync confirmed → test-case-design；独立任务 → null；selector 漂移授权豁免 → test-writing。

