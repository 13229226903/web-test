# AGENTS.md — web-test

本仓库是 UI 自动化测试编排骨架，5 个流水线角色以 skill 形式承载；本文件只做最小启动路由，完整运行规则按需读取 runtime 文件。

## 启动最小集

- **所有运行时**：先读 `artifacts/runtime/common.md`，再创建或恢复 `artifacts/<task_id>/state.md`、`progress.log`、`shots/` 与 `artifacts/.current_task`。
- **探索任务**：标准接力同时维护 `artifacts/<task_id>/exploration_report.md`（人审摘要）和 `artifacts/<task_id>/evidence/automation_handoff.yaml`（自动化交接）；不以报告替代 `sync.md`。
- **Codex 主控（默认）**：`artifacts/runtime/common.md` + `artifacts/runtime/orchestrator.md`；进入某阶段时必须完整读取 `skills/<role>/SKILL.md` 后，再按该 skill 执行该角色的一个 round。
- **Codex 隔离子代理（可选）**：用 multi-agent 子代理把角色拆到独立上下文；每个子代理只读 `artifacts/runtime/common.md` + `skills/<role>/SKILL.md` + 当前 state + 最近一次确认 artifact，返回结果由主控集成。

禁止启动时全量阅读所有历史 artifact 或所有 page_map。`AGENTS.md`、`rule.md`、`PROJECT.md`、历史 page_map 只按当前问题定向检索。

恢复或接力任务时，不得把历史 `state.md` / `sync.md` 中的 `exploration_driver: playwright_mcp_only` 当作当前会话工具可用性证明。若任务要求 Playwright MCP only，必须先在当前会话完成一次最小 Playwright MCP preflight（调用任一已暴露的 browser 工具）；未通过时记录 `playwright_mcp_unavailable` blocker 并停止，禁止静默降级为本地 Playwright、CDP 或 CUA。只有用户明确授权替代驱动后，才可如实改写 `exploration_driver` 并记录 progress。

Codex 执行时必须在 state.md 记录执行模式：
- 未用子代理：`execution_mode: codex_single_context`，同一上下文按角色顺序模拟；不得声称已启用子代理隔离。
- 用了子代理：`execution_mode: codex_subagent`，并在 `agent_call_count` 累加对应角色调用次数。

## 任务类型

- `new_feature_test`：新 PRD / 大改版 / 首次提测，必须需求先行。
- `existing_feature_first_exploration`：功能已存在但缺 confirmed page_map / sync / cases，先补页面资产。
- `stable_regression`：registry 已登记且 confirmed 资产齐全，优先复用脚本，仅漂移 / 差异 / 需求变更局部回退。
- `single_agent`：用户明确只要地图、用例、脚本或审查时，只执行对应角色，仍遵守该角色前置条件。

类型不确定时先根据 PRD、URL 和已有资产判断；仍无法判断才用一句话向用户确认。

## 权威运行规则

任务声明、Gate、差异 / skipped、共享红线、progress / journal、上下文控制见 `artifacts/runtime/common.md`。  
路由、状态机、角色 skill 执行、调用上限、接力与异常见 `artifacts/runtime/orchestrator.md`。

各角色规范已并入对应 `skills/<role>/SKILL.md`；根 `README.md` 是给人看的框架说明。


## 业务知识库运行时路由

- 业务任务初始化必须做**窄范围前置检索**，但禁止全量读取 `knowledge/`；先查 `knowledge/index.yaml`，再读取当前模块 / 页面 / 入口相关切片。
- 前置检索最多 2 个 Query、每次最多 5 条；MCP 探索运行时按需检索每次最多 4 条；异常兜底每次最多 3 条。
- `active` 可作为规则候选，`needs_verification` 只能作为探索提示；`conflict` / `superseded` / `retired` / `ui_residue` 不得作为默认业务断言。
- 角色不得自行扫描全量知识库。由 orchestrator 写入当前 `state.md` 的 `knowledge_context` 后，角色只读取与当前阶段相关的切片。
- 新经验先写当前任务 artifact 的 `knowledge_candidate`，归档 Gate 汇总并经用户确认后，才能写入正式知识切片。
- 业务知识库不保存密码、验证码、Cookie、Token、API key 等敏感值；`rule.md`、`PROJECT.md`、`page_map/` 和 confirmed artifact 仍是各自领域的权威来源。
