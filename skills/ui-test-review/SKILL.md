---
name: ui-test-review
description: 静态审查 test-writing 代码改动与 impl.md，对照 cases/page_map 和共享红线输出 pass/fail 结论。物理只读，不修代码、不跑测试。需要审查测试脚本时使用。
---

# review

> 共享契约（通用红线 / Artifact 接力 / progress / 项目约束）见 `artifacts/runtime/common.md`。

## 职责
静态审查 test-writing 代码改动与 impl.md，输出 pass / fail；不修代码、不跑测试、不改 artifact，结论由 orchestrator 落盘 review.md。

## 触发
- 用户主动审查；orchestrator 在 test-writing 收敛后派发。

## 输入
impl.md、git diff、相关 cases.md、confirmed sync.md、page_map 与 `automation_handoff.yaml`。

## Checklist
- 字段完整：有意义字段均已断言；未删除 / 弱化断言；expected 不为空 / `0` / `-`（共享红线）。
- 期望合理：expected 语义与 value 一致；文本断言避免过精确格式漂移。
- selector：无通配、`:nth-child`、位置 XPath、hash class（共享红线）。
- 架构：测试在 `tests/`，复用 PO / 数据驱动层，中文注释。
- 数据：数据外置 `data/*.yaml`，元素 ID 与 data / 代码一致。
- 引用：impl.md files_changed 与 git diff 一致；page_ref 真实存在；按钮用例用 `states.<state>.buttons.<button_id>`；代码动作与 handoff 的 `button_ref` / `driver` / `ready_when` 一致。
- 交接：handoff validator 已通过；page_map 版本与 cases / sync 一致；不存在代码阶段自行补出的账号态、状态链、selector、事件窗口或特殊 driver。
- 报告层级与截图：Allure 用 behaviors 树（epic / feature / title 与 cases.md 一致），不用 parentSuite / suite 代替主层级；每条矩阵 case 至少 1 截图或已写例外，否则按 Blocking 处理。

## review.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`status(completed)`、`inputs`、`outputs(verdict,blocking_issue_count,suggestion_count,next_agent)`。
- 正文：Blocking Issues、Suggestions、Checked Items。

## 判定
- Blocking Issues 非空 → `verdict=fail`；Suggestions 不影响 verdict。
- pass 且阻塞 0 → 提示 orchestrator 先派 test-writing(report-output) 生成并打开矩阵报告，用户确认后再进 regression-archive gate；fail → 回 test-writing 或 blocked。

## 循环约束
- 同一改动（impl.md / git diff）最多审查 3 轮；每轮 test-writing 自修后重审 1 次。
- 超限 orchestrator 标 `blocked_after_3_reviews`，等待用户，不无限回退重审。

## progress
- start / 每份输入 / done:review.md verdict。

## 业务知识库审查

- 只读取本次 `cases.md` / `impl.md` 实际引用的 `knowledge_id`，不全量读取知识库。
- 检查 `needs_verification` 是否被误当成确定断言，`retired` / `superseded` / `ui_residue` 是否被当作有效入口，以及知识冲突是否写入 sync / cases。
- 检查知识引用是否能追溯到 `source_refs`，账号态、历史校验、业务 expected 是否有有效来源。
- 发现可复用的新经验时提出 `knowledge_candidate`，不在 review 阶段直接改 active 知识。
