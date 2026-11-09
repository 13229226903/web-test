# 探索报告 — <功能名称>

> 面向用户审核的摘要；权威细节仍在同任务 `sync.md`、`page_map` 和 evidence。
> 格式红线：Bug 证据截图必须放在未展开的 HTML `<details>` 内，使用 `<img src="...">`；不得使用 Markdown 图片语法，且 `<details>` 内不要空行，避免渲染器把截图拆出折叠块导致默认展开。

## 1. 任务概览

- task_id: `<task_id>`
- task_type: `<new_feature_test | existing_feature_first_exploration | stable_regression | single_agent>`
- 入口: `<entry_url / entry_path>`
- 范围: `<scope>`
- 环境: `<test / predeploy / other>`
- 账号态: `<account states>`
- 平台: `<desktop / mobile / both>`
- 探索驱动: `<driver>`
- 当前状态: `pending_review`
- 关联产物:
  - sync: `artifacts/<task_id>/sync.md`
  - page_map: `<page_map_ref>`
  - automation_handoff: `artifacts/<task_id>/evidence/automation_handoff.yaml`
  - evidence: `artifacts/<task_id>/evidence/`

## 2. 探索范围与覆盖

| 覆盖域（AC / 覆盖点 / 用例） | 计划 | 实际 | 结论 | 证据 |
|---|---:|---:|---|---|
| `<入口 / 页面 / 状态 / AC 或覆盖点>` | `<n>` | `<n>` | `✅ / ⚠️ / ❌ / ⏭` | `<evidence>` |

汇总：`<n> covered · <n> gap · <n> bug_candidate · <n> skipped · <n> pending`

## 3. 关键入口与状态

| 覆盖点 | 入口 / page_ref | 账号 / 环境 | 关键动作与 ready 条件 | 结论 |
|---|---|---|---|---|
| `<case / AC>` | `<page_ref>` | `<account / env>` | `<action -> state>` | `covered / gap / bug_candidate / skipped` |

## 4. Bug Candidate

| AC / 用例名 | 标题 | 优先级 | 是否阻塞 | 明细 |
|---|---|---|---|---|
| `<AC-xxx 用例名>` | `<bug title>` | `<P0/P1/P2/P3>` | `<yes/no>` | [见 §9](#9-bug-candidate-明细可展开查看截图) |

> 无 bug 时写明“无”，并在 §9 保留章节和“无”。

## 5. Gap / Skipped / Pending

| 项目 | 类型 | 原因 | 是否阻塞 | 下一步 |
|---|---|---|---|---|
| `<item>` | `gap / skipped / pending` | `<reason>` | `<yes / no>` | `<action>` |

## 6. 自动化准备度

| 检查项 | 结果 |
|---|---|
| page_map 版本已锁定 | `✅ / ❌` |
| 每个覆盖点有 page_ref / button_ref | `✅ / ❌` |
| 账号态、环境、素材已确定 | `✅ / ❌` |
| 状态链和 ready / exit 条件已确定 | `✅ / ❌` |
| 特殊交互 driver 已确定 | `✅ / ❌` |
| Console / 统计事件采集边界已确定 | `✅ / ❌` |
| 没有未处理 blocking gap / bug | `✅ / ❌` |
| automation_handoff 状态 | `pending_review` |

## 7. 需要用户确认

1. `<范围 / 差异 / bug / skipped / 账号 / 风险>`

## 8. 已执行用例（按用例名标注）

- `<AC-xxx> <用例名> — covered`
- `<AC-xxx> <用例名> — bug_candidate`

> “已执行”包含 `covered` 与 `bug_candidate`；不得只给数量。

## 9. Bug Candidate 明细（可展开查看截图）

### `<AC-xxx> 用例名`

- 用例名：`<用例名>`
- 优先级：`<P0/P1/P2/P3>`
- [步骤]
  1. `<step>`
  2. `<step>`
- [结果] `<actual>`
- [期望] `<expected>`
- 证据截图：

<details>
<summary>点击展开：<AC-xxx> <截图说明></summary>
<img src="shots/<screenshot>.png" alt="<AC-xxx> <截图说明>" width="100%">
</details>

> 无 bug 时写“无”；有 bug 时每条必须包含对应用例名、步骤、实际、期望，并使用上述折叠截图格式。

## 10. 未执行用例（按用例名标注）

### 10.1 Gap（本轮未完成实测）

- `<AC-xxx> <用例名>`

### 10.2 Skipped（需失败注入、支付完成、额外账号或不可构造数据）

- `<AC-xxx> <用例名>`

> “未执行”必须区分 `gap` 与 `skipped`，按用例名逐条列出，不得只写统计数字。
