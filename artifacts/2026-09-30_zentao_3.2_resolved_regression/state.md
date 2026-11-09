---
task_id: 2026-09-30_zentao_3.2_resolved_regression
agent: orchestrator
status: in_progress
current_step: bug_regression
execution_mode: codex_single_context
task_type: regression_verify
human_gates_pending: []
created_at: 2026-09-30 11:20:20
updated_at: 2026-09-30 20:35:00
target_url: http://10.17.1.66:3001/
scope: 禅道 3.2 模块(moduleID=797) 创建人=梁锦润 且状态=已解决 的 bug 回归复核
source: http://bug.ad.com/zentao/bug-browse-205--byModule-797.html
environment: 测试服 http://10.17.1.66:3001 ; PC 端 Chrome 1920x1080 + 移动端 iPhone 13 仿真
account: 450832596@qq.com (User8JY) 验证码 123456 ; 新功能购买统计回归使用随机免费账号
exploration_driver: playwright_mcp_only
forbidden: 关闭 bug；修改 bug 状态；真实支付
regression_rule: 回归通过后仅用编辑表单填写 comment 备注「已回归」，不改状态、不关闭
blockers: []
---
# 回归清单
总计 44 条（PC 42 条 + 移动端 2 条）

## 已完成
- PASS：232349 / 232461 / 231590 / 232054 / 232241 / 232048 / 232248 / 231698（移动端）
- 设计如此：232407
- 无法验证：232453（VIP 免扣点，需免费账号复核扣点）
- FAIL：232593 / 232582

## 移动端
- 231698 已完成：移动端 AI 改图购买曝光/成功事件均已改为「新画布」，未捕获旧「画布页」事件
- 231943 待回归
