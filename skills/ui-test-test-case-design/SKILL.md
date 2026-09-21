---
name: ui-test-test-case-design
description: 解析 PRD/需求生成 requirement_draft，或基于 confirmed sync 与 versioned page_map 产出 L1~L6 可执行用例矩阵 cases.md。需要需求拆解或设计测试用例时使用。
---

# test-case-design

> 共享契约（通用红线 / Artifact 接力 / progress / 项目约束）见 `artifacts/runtime/common.md`。

## 职责
- 解析 PRD / 需求，形成可追溯的需求理解。
- 新功能：先 `requirement_draft` 初稿，提测后基于 confirmed sync + page_map 定稿 L1~L6 矩阵。
- 输出 cases.md；`requirement_draft` 默认 completed，`final_after_sync` 必须 pending_review。
- 不一定接 test-writing（用例可独立用于手工测试）。

## 触发
- 用户主动设计用例。
- 新功能：第一段 `phase=requirement_draft`（PRD 先行）；第二段 `phase=final_after_sync`（sync 确认后）。
- 存量补资产：sync 确认后 `phase=final_after_sync`。

## 输入
- 需求内容 / PRD 版本或追溯标识（缺失标 `PRD 版本未提供`）、task 范围。
- `requirement_draft`：不依赖 sync；只读 PRD。
- `final_after_sync`：必读 confirmed sync + page_map + PRD + `automation_handoff.yaml`，处理 `requirement_actual_diffs` / `bug_candidates`。

## phase 规则（新功能两段式）
- `requirement_draft`：PRD 是正确答案，输出需求理解、AC 映射、测试点初稿、预计状态、待提测清单；允许 `page_ref: TBD`；默认 completed；❌ 不允许进入 test-writing。
- `final_after_sync`：confirmed sync + page_map + PRD；补齐真实 page_ref / 步骤 / 等待 / 断言 / 截图点；✅ 用户确认后进入 test-writing。
- 新功能不得跳过 `requirement_draft` 直接用页面现状生成最终用例。
- `final_after_sync` 必须读取差异结论：`covered` 转用例；`gap`/`bug_candidate` 阻塞则标 `blocked_by_bug`；`skipped` 仅限环境 / 权限 / 风险并记录依赖。

## PRD 需求拆解（设计前必做）
需求理解至少提取：PRD 追溯信息、逐条 AC、入口与元素规格、状态机、业务规则、数据约束、异常 / 权限 / 兼容、特殊数据与依赖、风险操作、PRD-only 缺口。

## L1~L6
- L1 页面元素 / 结构 → `regression`
- L2 交互行为 / 状态迁移 → 默认全量
- L3 异常 / 权限 / 兼容 → 默认全量
- L4 PRD AC 逐条验证 → `regression`
- L5 数据边界值与等价类 → 默认全量
- L6 核心 Happy Path / E2E → `smoke`
- `execution_breakdown` 取值：`smoke` / `regression` / `default_full`；本项目不新增 `full` marker，不改 `pytest.ini`。

## 用例去重规则（合并同路径，不删 AC 覆盖）

- 去重只合并「同路径 / 同前置的重复断言」；任何 AC 的入口与期望都不得因去重而丢失。
- 保持 L1~L6 分层完整：删除某层用例前必须确认该层已被其他层等价覆盖，并在 cases.md 显式标注（如 L6 smoke 由 L2 覆盖）。
- 合并时保留所有等价入口：例如「分类卡片入口」与「左侧分类导航入口」是 AC 的不同入口，需在同一条内都覆盖，或分别落到 L2 / L6。
- 多值覆盖（热门标签 / 分类 / 计数等价类）在单条用例内循环覆盖，不依赖参数化展开，保证 `case_count` = Allure 报告用例数。

## 用例要求
- 每条用例可直接翻译为 Playwright：进入方式、操作（page_ref + 实际值 + 文件名）、等待、断言、截图点。
- 图片上传写 `test_images/` 具体文件名；人脸数量 / 分辨率边界不写“上传图片”。
- final 可自动化测试点必须关联 page_map 元素 / buttons 和 `automation_handoff.yaml` 的 `execution_contract_ref`；文案以需求为正确答案，页面不符记 bug_candidate。
- 购买 / 订阅 / credits 用例记录测试账号、环境、消耗、隔离 / reset 策略与回滚需求。
- 不得用“承接上一用例”“打开弹窗”“等待成功”等模糊步骤替代状态链；每一步必须能映射到 `button_ref`、实际值、ready_when 和 action_result。

## page_ref 规则
- `requirement_draft` 允许 `page_ref: TBD` / 预计位置；`final_after_sync` 必须替换为真实版本化 page_ref。
- 按钮优先引用 `states.<state>.buttons.<button_id>`；结构 / 文案可引用 elements / tabs / modals；多按钮链路列出关键按钮。

## 参数化 ID 规则
- L5 参数化标题显示实际值（如 `[最小值1]`、`[默认值20]`、`[最大值50]`）；禁止 `[None]` / `[最小值]` 无值 ID。
- 参数 ID 必须同时出现在 cases.md、Allure 标题与 pytest collect-only 输出。

## cases.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`phase(requirement_draft|final_after_sync)`、`status(completed|pending_review|confirmed)`、`inputs`、`outputs(case_count, priority_breakdown)`、`page_map_version`、`automation_handoff`、`next_agent`、`created_at`、`updated_at`。
- 正文按 Layer 分节输出（直观版）：
  - `## 需求理解`
  - `## L1 页面元素 / 结构（regression）`
  - `## L2 交互行为 / 状态迁移（default_full）`
  - `## L3 异常 / 权限 / 兼容（default_full）`
  - `## L4 PRD AC 逐条映射（regression）`
  - `## L5 数据边界与等价类（default_full）`
  - `## L6 核心 Happy Path / E2E（smoke）`
  - `## page_ref 与 selector 表`
  - `## 依赖缺口与风险`
- L1/L2/L3/L5/L6 用例表列：`ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点`。
- `步骤` 列必须写编号可执行步骤（1. 2. 3.），每步与 test-writing 的 `allure.step` 及测试 docstring 的 `测试步骤` 一一对应。
- `截图点` 列写截图名，供对应步骤内 `allure.attach(page.screenshot(), name="<截图点>")` 使用；每个有语义的断言 / 状态变化都应有对应截图点，做到「每条断言一一对应截图」。
- `测试点` 列即短标题，供 `@allure.title("L{N}-{NNN}: <测试点>")` 使用。
- L4 为 AC 映射表：`AC | 摘要 | 覆盖用例 | 期望/缺口`。
- 各节 ID 前缀统一；L5 参数化标题显示实际值，禁止 `[None]`/`[最小值]` 无值 ID。

## 自动化交接要求

- `final_after_sync` 产出的每条可自动化用例必须填 `execution_contract_ref`，指向 `automation_handoff.yaml#<case_id>`。
- cases 的 `page_map_version` 必须与 handoff、sync 当前输入一致；任何 page_map / sync / cases 修订都必须使 handoff 回退为 `ready_for_case_design`，重新确认后才能写代码。
- 合并多个统计事件或等价路径时，必须保留每个动作的独立 `state_chain`、`event_capture` 和截图 / Console 证据；不能只在一行写“同链路合并”。
- 用例确认前运行：

```powershell
python scripts/validate_automation_handoff.py --handoff artifacts/<task_id>/evidence/automation_handoff.yaml --sync artifacts/<task_id>/sync.md --cases artifacts/<task_id>/cases.md
```

校验失败时退回 page-map-sync 或本角色，不得让 test-writing 自行补缺失的业务事实。

## Human Gate
- `requirement_draft` 默认 completed（除非用户要先审）；`final_after_sync` 必须 pending_review，用户确认后 confirmed。
- 只有 `phase=final_after_sync` 且 confirmed 后，orchestrator 才接力 test-writing。

## 角色红线（共享红线见 common.md）
- 不引用 page_map 不存在的元素；`final_after_sync` 中 PRD-only 不得编造 page_ref。
- L5 不得只写“最小 / 默认 / 最大”标签，必须写实际值与预期。
- 不隐藏破坏性 / 对外通知 / 影响真实用户 / 难以回滚 / 跨端 / 特殊数据风险。
- 不写代码；不修改其他 artifact；不替用户决定“用例够不够”（一律 pending_review）。
- 不新增或修改 pytest marker；不省略 progress.log。

## 循环约束
- 同一 task 内最多 2 个 phase：新功能 `requirement_draft` + `final_after_sync` 各 1 次；`final_after_sync` 第 2 次仍失败，orchestrator 标 blocked，等待用户。
- 禁止反复重写 cases.md 绕过 pending_review；未确认不得进入 test-writing。

## progress
- start / step:loaded <file> / step:prd_parsed / step:loaded automation_handoff / step:designed N cases / gate:cases_review / done:cases.md+handoff_checked

## 上下游
- 上游：orchestrator（draft 不要求 sync；final 要求 sync confirmed）。
- 下游：final 确认后 → test-writing；draft 完成后 → page-map-sync 或等待提测；仅要用例 → null。

## 输出格式
- 表格用 markdown 表格；`步骤` 列为编号可执行清单（1. 2. 3.），每步对应 test-writing 的 `allure.step` 与测试 docstring 的 `测试步骤`。
- `截图点` 列写截图名，供对应步骤内 `allure.attach(page.screenshot(), name="<截图点>")` 使用，并做到每个有语义的断言 / 状态变化都有对应截图点；`测试点` 列即短标题，供 `@allure.title("L{N}-{NNN}: <测试点>")` 使用。
- 期望可断言，避免“正常显示”类模糊词。
- 上传 / 生成 / credits 用例写明登录、环境顺序、数据与授权要求。
- AI 审查列为“是”时写明确视觉判断目标；Allure 用中文标题 / 描述 / 步骤并标注 Layer。

## 业务知识库使用

- `requirement_draft` 可读取前置 `knowledge_context` 补全 PRD 未说明的旧入口、历史规则、账号态和校验，但必须标为 `legacy_candidate` / `needs_verification`，不得伪装成新的 PRD AC。
- `final_after_sync` 只消费与 confirmed `sync.md`、versioned `page_map` 一致的知识；知识库命中须映射到真实 `page_ref` 或当前任务证据。
- 每条由历史业务规则驱动的用例，至少追溯到 `knowledge_id`、confirmed `sync.md` / `page_map` 或用户明确需求之一。
- 知识库与 PRD / 页面冲突时，保留新需求预期和页面实际差异，标记 `gap` / `bug_candidate`，不得用历史知识抹平冲突。
- 发现新的可复用业务经验时只提交 `knowledge_candidate`，不直接修改知识库 active 切片。
