import io
p = r"skills\ui-test-test-case-design\SKILL.md"
s = io.open(p, encoding="utf-8").read()
old = """## cases.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`phase(requirement_draft|final_after_sync)`、`status(completed|pending_review|confirmed)`、`inputs`、`outputs(case_count, priority_breakdown)`、`next_agent`、`created_at`、`updated_at`。
- 矩阵列：`case_id`、`Layer`、`策略`、`标题`、`进入方式`、`操作`、`等待`、`断言`、`截图点`、`AI 审查`、`page_ref`。
- 正文：需求理解、L1~L6 矩阵、依赖缺口、风险与授权请求。"""
new = """## cases.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`phase(requirement_draft|final_after_sync)`、`status(completed|pending_review|confirmed)`、`inputs`、`outputs(case_count, priority_breakdown)`、`next_agent`、`created_at`、`updated_at`。
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
- L4 为 AC 映射表：`AC | 摘要 | 覆盖用例 | 期望/缺口`。
- 各节 ID 前缀统一；L5 参数化标题显示实际值，禁止 `[None]`/`[最小值]` 无值 ID。"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("SKILL.md cases.md 结构已改为按 Layer 分节")
