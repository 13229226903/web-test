# skills/ —— 角色 skill 索引与格式规范

本目录承载 5 个流水线角色的执行规范。每个 skill 是**内网单仓库**使用的角色 SOP，
与 `artifacts/runtime/common.md`、`artifacts/runtime/orchestrator.md` 强耦合。

## 角色索引

| 角色 | skill | 主要产物 | 上游 | 下游 |
|---|---|---|---|---|
| page-map-sync | `ui-test-page-map-sync/SKILL.md` | `page_map/*.yaml` + `sync.md` + `exploration_report.md` + `automation_handoff.yaml` | orchestrator | test-case-design / test-writing（漂移豁免） |
| test-case-design | `ui-test-test-case-design/SKILL.md` | `requirement_draft` / `cases.md` | orchestrator | test-writing |
| test-writing | `ui-test-test-writing/SKILL.md` | `tests/*.py` + `data/*.yaml` + `impl.md` | test-case-design | review |
| review | `ui-test-review/SKILL.md` | `review.md` | test-writing | test-writing(report-output) / regression-archive |
| visual-review | `ui-test-visual-review/SKILL.md` | `visual_review.md` | review | regression-archive |

## 格式标准

所有 SKILL.md 必须遵循同一顶层骨架，正文长度按角色职责自适应——**不为了凑格式写长文**。

### frontmatter

```yaml
---
name: ui-test-<role>          # 必须与目录名一致
description: <能力 + 触发场景 + 明确边界，一段话>
---
```

只保留运行时真正消费的字段。不引入 slug / displayName / version 等未被消费的字段。

### 必备章节（按顺序）

| # | 章节 | 用途 |
|---|---|---|
| 1 | `## 职责` + `## 触发` | 这个角色做什么、何时触发 |
| 2 | `## 输入契约` | 上游必须提供什么、缺什么就拒绝 |
| 3 | `## 输出契约` | 标准产物名 / 路径 / 状态 |
| 4 | `## 红线` | 该角色绝不允许做的事 |
| 5 | `## 上下游` | 上游 / 下游 / 回退目标 |
| 6 | `## progress` | progress.log 事件格式 |
| 7 | `## 业务知识库使用` | 知识切片消费边界 |

### 推荐章节（按需，有则保留在骨架内）

| 章节 | 用途 |
|---|---|
| `## 不适用场景` | 防误用（When NOT to Use） |
| `## 工作流` | 可执行步骤 |
| `## 前置检查` | 入口 gate 条件 |
| `## Gate 与判定` | pass/fail 判定与人工 gate |
| `## 失败分类` | 失败归因与回退路径 |
| `## Common Mistakes` | 历史高频错误与替代做法 |
| `## 循环约束` | 重试 / 回退次数上限 |

### 写作规则

- 跨角色共享规则放 `artifacts/runtime/common.md`，不在每个 skill 里重复。
- 项目事实（账号 / 入口 / 素材）放 `PROJECT.md`；技术避坑放 `rule.md`。
- 正文只引用，不复述其它文件已有的大段内容。
- 章节内允许用 H3 承载角色专属细则（如 handoff 定位契约、taskId 记录）。

## 校验

```bash
python scripts/validate_skills.py
```

校验内容：frontmatter 完整性、必备章节存在、章节顺序、目录名与 name 一致、
被引用的 runtime / artifact 路径存在。
