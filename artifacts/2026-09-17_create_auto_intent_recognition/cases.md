---
task_id: 2026-09-17_create_auto_intent_recognition
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  requirement: user prompt in this thread
  sync: artifacts/2026-09-17_create_auto_intent_recognition/sync.md
  page_map: page_map/pokecut/create_chat_to_edit_auto_v1.yaml
  evidence: artifacts/2026-09-17_create_auto_intent_recognition/evidence/auto_intent_results.yaml
outputs:
  case_count: 11
  priority_breakdown:
    P0: 11
    P1: 0
  deduped: true
  dedupe_strategy: L2 交互链路并入 L6 各 prompt 用例；L5 分辨率等价类并入 L6 各 prompt 用例；仅保留 L1 页面结构与 L6 十条核心生成链路。
next_agent: test-writing
created_at: 2026-09-17 03:05:00
updated_at: 2026-09-17 03:10:00
---

## 需求理解

- 入口：`http://10.17.1.66:3001/create`
- 功能：`Chat to Edit` 输入框 + `Auto` 模型 + 1 张参考图 + 10 条指定 prompt
- 账号：会员账号 `450832596@qq.com`，页面显示 `User8JY`
- 参考图：`test_images/1K.jpg`，原始分辨率 `1200x1600`
- 核心验证点：
  1. 提交任务成功并记录 `taskId`
  2. `AutoIntentRecognition` 返回的 `styleId` 与预期一致
  3. 画布结果图分辨率符合预期
- 特殊规则：
  - `enhance` / `人像增强` / `文字增强` → 4K
  - `老照片修复` → ×2
  - `去水印` / `穿上比基尼` / `去除眼袋` / `增肌` / `变成光头` → 同原图
  - `背景换成沙滩` → `styleId` 为空，仅记录 `taskId`

## L1 页面元素 / 结构（regression）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| L1-001 | P0 | Create 页 Chat to Edit 结构与默认态 | `page_map/pokecut/create_chat_to_edit_auto_v1.yaml: elements.chat_to_edit_prompt/upload_reference_images/model_selector/submit_task, states.create_initial.buttons.upload_reference_images/model_selector` | 1. 会员账号登录后访问 `/create`。<br>2. 等待 `Chat to Edit` 标题可见。<br>3. 断言 prompt 输入框、上传按钮、Model 选择器、Setting、提交图标可见。<br>4. 断言默认模型为 `Nano Banana 2 Lite`，字数为 `0/3000`。 | 页面 10s | 标题、输入框、上传、模型、提交图标全部可见；默认模型与字数正确 | `L1-001_create_structure.png` |

## L2 交互行为 / 状态迁移（default_full）

> 去重说明：`上传 → 选择 Auto → 输入 prompt → 提交 → 跳转画布 → 结果显示` 的完整状态迁移已并入 `L6-001` ~ `L6-010`，不再单列重复用例。

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---|---|---|---|---|---|
| — | — | 已合并 | — | 见 L6-001 ~ L6-010 | — | 不重复生成任务、不重复上传同一素材 | — |

## L3 异常 / 权限 / 兼容（default_full）

> 按用户确认删除 `L3-001`；本轮不覆盖 0 credits / 未登录拦截分支。

- 生成类任务消耗 credits；必须使用会员账号 `450832596@qq.com`
- `taskId` / `styleId` 需从控制台日志提取，测试脚本需监听 console 或 network
- 结果分辨率需选中结果图后读取，不得仅依赖页面标题
- 第 10 条用例不验证分辨率，避免超出需求范围
