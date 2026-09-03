---
name: ui-test-visual-review
description: 读取截图与 cases/impl 中的视觉期望，通过多模态 API 判定 pass/fail/partial，补足 DOM 断言无法覆盖的视觉审查。需要视觉审查时使用。
---

# visual-review

> 共享契约（通用红线 / Artifact 接力 / progress / 项目约束）见 `artifacts/runtime/common.md`。

## 职责
读取 Allure 截图与 cases / impl 中的视觉期望，用多模态 API 判定 pass / fail / partial，补足 DOM 无法断言的视觉点。不修代码、不跑测试、不改 artifact，结论由 orchestrator 落盘 visual_review.md。

## 触发
- orchestrator 在 review pass 后、存在视觉期望用例时派发。
- 用户主动审查截图。

## 输入
- cases.md（含视觉期望用例）。
- `data/screenshots/<task_id>/` 截图。
- impl.md（“仅截图”断言标注）。

## 工作流
1. 识别视觉期望用例（颜色变化、元素出现 / 消失、翻转 / 旋转、拖拽、布局 / 网格）。
2. 对照 impl.md 截图断言，只审查 DOM 无法覆盖的点。
3. 逐个用例执行：
   `python scripts/visual_check.py --before <before.png> --after <after.png> --expectation "<期望>"`
   返回 `{"verdict": "pass|fail|uncertain", "reason": "..."}`。
4. 汇总判定并输出结论。
- 用 API 而非 agent 看图：`visual_check.py` 调多模态 API（OpenAI 兼容）。模型 / base URL 解析以 `helpers/review_api_config.py` 为准：优先 `OPENAI_API_KEY`（`OPENAI_MODEL`，代码默认 `gpt-4.1`），回退 Anthropic；`conftest.visual_assert` 未配置时默认 `gpt-5.6`。

## 视觉判定规则
- 颜色变化 / 元素出现消失 / 翻转旋转 / 滑块拖拽 / 布局网格：对比前后截图，判断目标区域是否符合期望；证据不足标 uncertain。

## visual_review.md 结构（字段表）
- frontmatter：`task_id`、`agent`、`status`、`inputs`、`outputs(verdict,visual_case_count,passed,failed,uncertain,blocking_issue_count,next_agent)`。
- 正文：逐用例判定（前后截图、期望、判定、置信度）。

## 判定
- pass：全部符合，可进入 regression-archive gate。
- fail：存在明确不符，测试结果必须传导失败。
- partial / uncertain：证据不足不强行 pass，交人工复核。

## 红线
- 不修代码、不跑测试、不改 artifact。
- 不确定标 uncertain，不强行 pass / fail。
- 不省略 progress.log。

## 循环约束
- 同一视觉点最多判定 2 次；第 2 次仍 fail / partial，传导 `blocked` 或交人工复核，不无限重跑视觉审查。

## progress
- start / step:reviewed <case> <pass|fail|uncertain> / done:visual_review.md verdict=<pass|fail|partial>

## 上下游与归档 gate
- 上游：orchestrator（review pass 后）。
- 下游：pass → 提示 orchestrator 可进 regression-archive gate；fail / partial → 人工复核或回 test-writing / cases。
- 本角色不归档、不更新 registry。

## 对 test-writing 的约定
- test-writing 在 impl.md 标注“仅截图”断言（如 `[视觉断言: 文字背景变红]`），本角色据此只审查 DOM 无法覆盖的点。
