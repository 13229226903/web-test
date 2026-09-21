# 探索报告 — <功能名称>

> 面向用户审核的摘要；权威细节仍在同任务 `sync.md`、`page_map` 和 evidence。

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

### Bug `<N>`｜<标题>

- 影响范围: `<case / AC / module>`
- 步骤:
  1. `<step>`
  2. `<step>`
- 实际: `<actual>`
- 期望: `<expected>`
- 证据: `<screenshot / console / DOM>`
- 是否阻塞自动化: `<yes / no>`

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

## 8. 关联产物

- sync: `artifacts/<task_id>/sync.md`
- page_map: `<page_map_ref>`
- automation_handoff: `artifacts/<task_id>/evidence/automation_handoff.yaml`
- evidence: `artifacts/<task_id>/evidence/`

