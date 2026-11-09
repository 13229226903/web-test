---
task_id: 2026-09-24_zentao_3.2_bug_regression
agent: orchestrator
status: in_progress
current_step: bug_regression
execution_mode: codex_single_context
task_type: regression_verify
human_gates_pending: []
handoff_status: pending_review
created_at: 2026-09-24 17:24:31
updated_at: 2026-09-24 17:24:31
target_url: http://10.17.1.66:3001/
scope: 禅道 3.2 模块(moduleID=797) 创建人=梁锦润 且状态=已解决 的 15 条 bug 回归复核
source: http://bug.ad.com/zentao/bug-browse-205--byModule-797.html
environment: 测试服 http://10.17.1.66:3001 ; PC 端 Chrome 1920x1080
account: 450832596@qq.com (User8JY) 验证码 123456
exploration_driver: playwright_mcp_only
forbidden: 关闭 bug；修改 bug 状态；真实支付
regression_rule: 回归通过后仅用编辑表单填写 comment 备注「已回归」，不改状态、不关闭
blockers: []
---
# 回归清单（已解决 15 条）
- 232116 背景更改弹窗 confirm 点击没反应
- 232082 从背景移除 SEO 进画布一直 loading
- 232058 multi mode 开关点击没反应
- 232057 Multi Model 上传参考图没取最小上限
- 232056 多选模型后选灵感预设，模型列表状态有误
- 232054 Crop 锁定后仍可单独修改宽高（设计如此）
- 232052 旋转角度常驻显示
- 232051 auto 模型历史记录数据不对
- 232050 批量提交 auto，新图层没错开
- 232048 点击抠图历史记录会选中图层并展开弹窗（设计如此）
- 232045 生图历史记录缩略图显示异常
- 232043 刷新页面图层都没了
- 232040 Multi Mode 单模型 Pro 图生图仍显示比例选项（设计如此）
- 232031 create 页开 Multi Mode 进画布变关闭
- 232020 取消默认模型后入口填充模型不对
# 排除（已关闭 4 条）
- 232343 / 232047 / 232044 / 231997
